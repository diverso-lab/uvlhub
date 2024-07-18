import os
from app.modules.orcid.repositories import OrcidRepository
from core.services.BaseService import BaseService
from flask import current_app
from authlib.integrations.flask_client import OAuth

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
            name='orcid',
            client_id=self.client_id,
            client_secret=self.client_secret,
            access_token_url='https://orcid.org/oauth/token',
            authorize_url='https://orcid.org/oauth/authorize',
            client_kwargs={
                'scope': '/authenticate /read-limited',
                'token_endpoint_auth_method': 'client_secret_post'
            }
        )
        return oauth, orcid
