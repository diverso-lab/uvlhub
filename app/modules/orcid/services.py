import os
from app.modules.orcid.repositories import OrcidRepository
from core.services.BaseService import BaseService
from flask import current_app
from authlib.integrations.flask_client import OAuth
from app import db
from app.modules.auth.models import User
from app.modules.profile.models import UserProfile
from app.modules.orcid.models import Orcid


class OrcidService(BaseService):

    def __init__(self):
        super().__init__(OrcidRepository())
        self.client_id = self.get_orcid_client_id()
        self.client_secret = self.get_orcid_client_secret()
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
        resp = self.orcid_client.get("https://orcid.org/oauth/userinfo", token=token)
        return resp.json()

    def get_or_create_user(self, user_info):
        orcid_id = user_info["sub"]
        given_name = user_info.get("given_name", "")
        family_name = user_info.get("family_name", "")
        affiliation = user_info.get("affiliation", "")

        orcid_record = Orcid.query.filter_by(orcid_id=orcid_id).first()

        if orcid_record:
            profile = UserProfile.query.filter_by(id=orcid_record.profile_id).first()
            if profile:
                user = User.query.get(profile.user_id)
                return user
        else:
            user = User()
            user.set_password(orcid_id)
            db.session.add(user)
            db.session.commit()

            profile = UserProfile(
                user_id=user.id,
                name=given_name,
                surname=family_name,
                affiliation=affiliation,
            )
            db.session.add(profile)
            db.session.commit()

            orcid_record = Orcid(orcid_id=orcid_id, profile_id=profile.id)
            db.session.add(orcid_record)
            db.session.commit()

            return user
