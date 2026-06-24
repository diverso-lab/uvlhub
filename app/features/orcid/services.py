import os
import secrets

from authlib.integrations.flask_client import OAuth
from flask import current_app
from splent_framework.services.BaseService import BaseService
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.features.auth.repositories import UserRepository
from app.features.orcid.repositories import OrcidRepository
from app.features.profile.repositories import UserProfileRepository


class OrcidService(BaseService):

    def __init__(self):
        super().__init__(OrcidRepository())
        self.user_repository = UserRepository()
        self.user_profile_repository = UserProfileRepository()
        self.client_id = self.get_orcid_client_id()
        self.client_secret = self.get_orcid_client_secret()

        if not self.client_id or not self.client_secret:
            current_app.logger.error("ORCID_CLIENT_ID/ORCID_CLIENT_SECRET not configured")

        self.oauth, self.orcid_client = self.configure_oauth(current_app)

    def get_orcid_client_id(self):
        return os.getenv("ORCID_CLIENT_ID")

    def get_orcid_client_secret(self):
        return os.getenv("ORCID_CLIENT_SECRET")

    def configure_oauth(self, app):
        oauth = OAuth(app)
        orcid = oauth.register(
            name="orcid",
            client_id=self.client_id,
            client_secret=self.client_secret,
            access_token_url="https://orcid.org/oauth/token",
            authorize_url="https://orcid.org/oauth/authorize",
            client_kwargs={
                "scope": "/authenticate",
                "token_endpoint_auth_method": "client_secret_post",
            },
        )
        return oauth, orcid

    def get_orcid_user_info(self, token):
        try:
            resp = self.orcid_client.get("https://orcid.org/oauth/userinfo", token=token)
        except Exception as exc:
            current_app.logger.exception("ORCID userinfo request failed: %s", exc)
            return None, "Could not reach ORCID. Please try again."

        if not resp:
            current_app.logger.error("ORCID userinfo empty response")
            return None, "ORCID did not return user information. Please try again."

        if resp.status_code != 200:
            current_app.logger.error("ORCID userinfo failed (%s): %s", resp.status_code, getattr(resp, "text", None))
            if resp.status_code == 429:
                return None, "ORCID is rate-limiting requests. Please try again in a minute."
            return None, "ORCID user information request failed. Please try again."

        data = resp.json() or {}
        orcid_id = (data.get("sub") or "").strip()
        if not orcid_id:
            current_app.logger.error("ORCID userinfo missing 'sub': %s", data)
            return None, "ORCID did not provide an ORCID iD. Please try again."

        return data, None

    def _existing_user_for_orcid(self, orcid_id: str):
        orcid_record = self.repository.get_by_orcid_id(orcid_id)
        if not orcid_record:
            return None, orcid_record
        profile = self.user_profile_repository.get_by_id(orcid_record.profile_id)
        user = self.user_repository.get_by_id(profile.user_id) if profile else None
        return user, orcid_record

    def get_or_create_user(self, user_info):
        if not user_info:
            return None, "Missing ORCID user information."

        orcid_id = (user_info.get("sub") or "").strip()
        if not orcid_id:
            return None, "Missing ORCID iD."

        given_name = (user_info.get("given_name") or "").strip()
        family_name = (user_info.get("family_name") or "").strip()
        affiliation = (user_info.get("affiliation") or "").strip()

        try:
            user, orcid_record = self._existing_user_for_orcid(orcid_id)
            if user:
                return user, None
            if orcid_record:
                # Dangling link with no user behind it: drop it and start fresh.
                self.repository.delete(orcid_record.id)
                self.repository.session.flush()

            user = self.user_repository.create(commit=False, password=secrets.token_urlsafe(24), active=True)
            profile = self.user_profile_repository.create(
                commit=False, user_id=user.id, name=given_name, surname=family_name, affiliation=affiliation
            )
            self.repository.create(commit=False, orcid_id=orcid_id, profile_id=profile.id)
            self.repository.session.commit()
            return user, None

        except IntegrityError as exc:
            # Two concurrent callbacks racing to create the same ORCID account.
            current_app.logger.warning("IntegrityError creating ORCID user (%s): %s", orcid_id, exc)
            self.repository.session.rollback()
            user, _ = self._existing_user_for_orcid(orcid_id)
            if user:
                return user, None
            return None, "Could not create your account due to a concurrency issue. Please try again."

        except SQLAlchemyError as exc:
            current_app.logger.exception("Database error creating ORCID user (%s): %s", orcid_id, exc)
            self.repository.session.rollback()
            return None, "Could not create your account due to a database error. Please try again."
