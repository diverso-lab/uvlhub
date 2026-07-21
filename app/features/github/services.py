import os
import secrets

from authlib.integrations.flask_client import OAuth
from flask import current_app
from splent_framework.services.BaseService import BaseService
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.features.auth.repositories import UserRepository
from app.features.github.repositories import GithubRepository
from app.features.profile.repositories import UserProfileRepository


class GithubService(BaseService):

    def __init__(self):
        super().__init__(GithubRepository())
        self.user_repository = UserRepository()
        self.user_profile_repository = UserProfileRepository()
        self.client_id = self.get_github_client_id()
        self.client_secret = self.get_github_client_secret()

        if not self.client_id or not self.client_secret:
            current_app.logger.warning("GITHUB_CLIENT_ID/GITHUB_CLIENT_SECRET not configured; GitHub login disabled")

        self.oauth, self.github_client = self.configure_oauth(current_app)

    def get_github_client_id(self):
        return os.getenv("GITHUB_CLIENT_ID")

    def get_github_client_secret(self):
        return os.getenv("GITHUB_CLIENT_SECRET")

    def configure_oauth(self, app):
        oauth = OAuth(app)
        github = oauth.register(
            name="github",
            client_id=self.client_id,
            client_secret=self.client_secret,
            access_token_url="https://github.com/login/oauth/access_token",
            authorize_url="https://github.com/login/oauth/authorize",
            client_kwargs={"scope": "user:email"},
        )
        return oauth, github

    def get_github_user_info(self, token):
        try:
            resp = self.github_client.get("https://api.github.com/user", token=token)
        except Exception as exc:
            current_app.logger.exception("GitHub userinfo request failed: %s", exc)
            return None, "Could not reach GitHub. Please try again."

        if not resp:
            current_app.logger.error("GitHub userinfo empty response")
            return None, "GitHub did not return user information. Please try again."

        if resp.status_code != 200:
            current_app.logger.error("GitHub userinfo failed (%s): %s", resp.status_code, getattr(resp, "text", None))
            if resp.status_code == 429:
                return None, "GitHub is rate-limiting requests. Please try again in a minute."
            return None, "GitHub user information request failed. Please try again."

        data = resp.json() or {}
        github_id = data.get("id")
        if not github_id:
            current_app.logger.error("GitHub userinfo missing 'id': %s", data)
            return None, "GitHub did not provide a user ID. Please try again."

        return data, None

    def _existing_user_for_github(self, github_id: int):
        github_record = self.repository.get_by_github_id(github_id)
        if not github_record:
            return None, github_record
        profile = self.user_profile_repository.get_by_id(github_record.profile_id)
        user = self.user_repository.get_by_id(profile.user_id) if profile else None
        return user, github_record

    def get_or_create_user(self, user_info):
        if not user_info:
            return None, "Missing GitHub user information."

        github_id = user_info.get("id")
        if not github_id:
            return None, "Missing GitHub ID."

        github_login = (user_info.get("login") or "").strip()
        name = (user_info.get("name") or "").strip()
        if not name:
            name = github_login

        email = (user_info.get("email") or "").strip().lower() if user_info.get("email") else None

        try:
            from app.features.auth.repositories import ExternalIdentityRepository

            external_repo = ExternalIdentityRepository()

            # 1. Check if this GitHub ID already exists
            existing_identity = external_repo.get_by_provider_id("github", github_id)
            if existing_identity and existing_identity.user_id:
                user = self.user_repository.get_by_id(existing_identity.user_id)
                if user:
                    return user, None

            # 2. Check if email exists in ExternalIdentity
            if email:
                email_identity = external_repo.get_by_email(email)
                if email_identity and email_identity.user_id:
                    user = self.user_repository.get_by_id(email_identity.user_id)
                    if user:
                        # Link this GitHub account to existing user
                        external_repo.create(
                            commit=False, user_id=user.id, provider="github", provider_id=github_id, email=email
                        )
                        self.repository.create(
                            commit=False, github_id=github_id, github_login=github_login, profile_id=user.profile.id
                        )
                        self.repository.session.commit()
                        return user, None

            # 3. Check if email exists in User table
            if email:
                existing_user = self.user_repository.get_by_email(email)
                if existing_user:
                    # Link GitHub to existing user
                    external_repo.create(
                        commit=False, user_id=existing_user.id, provider="github", provider_id=github_id, email=email
                    )
                    self.repository.create(
                        commit=False,
                        github_id=github_id,
                        github_login=github_login,
                        profile_id=existing_user.profile.id,
                    )
                    self.repository.session.commit()
                    return existing_user, None

            # 4. Create new user if nothing found
            user = self.user_repository.create(
                commit=False, password=secrets.token_urlsafe(24), active=True, email=email
            )
            profile = self.user_profile_repository.create(commit=False, user_id=user.id, name=name, surname="")
            self.repository.create(commit=False, github_id=github_id, github_login=github_login, profile_id=profile.id)
            external_repo.create(commit=False, user_id=user.id, provider="github", provider_id=github_id, email=email)
            self.repository.session.commit()
            return user, None
        except IntegrityError as exc:
            current_app.logger.warning("IntegrityError creating GitHub user (%s): %s", github_id, exc)
            self.repository.session.rollback()
            user, _ = self._existing_user_for_github(github_id)
            if user:
                return user, None
            return None, "Could not create your account due to a concurrency issue. Please try again."

        except SQLAlchemyError as exc:
            current_app.logger.exception("Database error creating GitHub user (%s): %s", github_id, exc)
            self.repository.session.rollback()
            return None, "Could not create your account due to a database error. Please try again."
