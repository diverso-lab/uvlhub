import os
import secrets
from sqlite3 import IntegrityError

from authlib.integrations.flask_client import OAuth
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

from app import db
from app.modules.auth.models import User
from app.modules.orcid.models import Orcid
from app.modules.orcid.repositories import OrcidRepository
from app.modules.profile.models import UserProfile
from core.services.BaseService import BaseService

ORCID_ENABLED = False


class OrcidService(BaseService):

    def __init__(self):
        super().__init__(OrcidRepository())

        self.enabled = ORCID_ENABLED
        self.client_id = None
        self.client_secret = None
        self.oauth = None
        self.orcid_client = None

        if not self.enabled:
            return

        self.client_id = self.get_orcid_client_id()
        self.client_secret = self.get_orcid_client_secret()

        if not self.client_id or not self.client_secret:
            current_app.logger.warning("ORCID is enabled but ORCID_CLIENT_ID/ORCID_CLIENT_SECRET are not configured")
            return

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
        if not self.enabled or self.orcid_client is None:
            return None, "ORCID authentication is disabled."

        try:
            resp = self.orcid_client.get("https://orcid.org/oauth/userinfo", token=token)
        except Exception as exc:
            current_app.logger.exception("ORCID userinfo request failed: %s", exc)
            return None, "Could not reach ORCID. Please try again."

        if not resp:
            current_app.logger.error("ORCID userinfo empty response")
            return None, "ORCID did not return user information. Please try again."

        if resp.status_code != 200:
            current_app.logger.error(
                "ORCID userinfo failed (%s): %s",
                resp.status_code,
                getattr(resp, "text", None),
            )

            if resp.status_code == 429:
                return None, "ORCID is rate-limiting requests. Please try again in a minute."

            return None, "ORCID user information request failed. Please try again."

        data = resp.json() or {}

        orcid_id = (data.get("sub") or "").strip()
        if not orcid_id:
            current_app.logger.error("ORCID userinfo missing 'sub': %s", data)
            return None, "ORCID did not provide an ORCID iD. Please try again."

        return data, None

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
            orcid_record = Orcid.query.filter_by(orcid_id=orcid_id).first()
            if orcid_record:
                profile = UserProfile.query.get(orcid_record.profile_id)
                user = User.query.get(profile.user_id) if profile else None

                if user:
                    return user, None

                db.session.delete(orcid_record)
                db.session.flush()

            user = User(
                password=generate_password_hash(secrets.token_urlsafe(24)),
                active=True,
            )
            db.session.add(user)
            db.session.flush()

            profile = UserProfile(
                user_id=user.id,
                name=given_name,
                surname=family_name,
                affiliation=affiliation,
            )
            db.session.add(profile)
            db.session.flush()

            orcid_record = Orcid(orcid_id=orcid_id, profile_id=profile.id)
            db.session.add(orcid_record)

            db.session.commit()
            return user, None

        except IntegrityError as exc:
            current_app.logger.warning("IntegrityError creating ORCID user (%s): %s", orcid_id, exc)
            db.session.rollback()

            try:
                orcid_record = Orcid.query.filter_by(orcid_id=orcid_id).first()
                if orcid_record:
                    profile = UserProfile.query.get(orcid_record.profile_id)
                    user = User.query.get(profile.user_id) if profile else None
                    if user:
                        return user, None
            except Exception as reread_exc:
                current_app.logger.exception("Failed to reread ORCID user after IntegrityError: %s", reread_exc)

            return None, "Could not create your account due to a concurrency issue. Please try again."

        except SQLAlchemyError as exc:
            current_app.logger.exception("Database error creating ORCID user (%s): %s", orcid_id, exc)
            db.session.rollback()
            return None, "Could not create your account due to a database error. Please try again."