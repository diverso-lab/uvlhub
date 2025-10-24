import os
import secrets

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
        # Valida respuesta
        resp = self.orcid_client.get("https://orcid.org/oauth/userinfo", token=token)
        if not resp or resp.status_code != 200:
            current_app.logger.error("ORCID userinfo fallo: %s", getattr(resp, "text", None))
            return None
        data = resp.json() or {}
        # 'sub' es el ORCID iD en OIDC
        if "sub" not in data:
            current_app.logger.error("ORCID userinfo sin 'sub': %s", data)
            return None
        return data

    def get_or_create_user(self, user_info):
        if not user_info:
            return None

        orcid_id = (user_info.get("sub") or "").strip()
        if not orcid_id:
            return None

        given_name = user_info.get("given_name") or ""
        family_name = user_info.get("family_name") or ""
        affiliation = user_info.get("affiliation") or ""  # si no existe, queda ""

        try:
            # 1) ¿Existe registro ORCID?
            orcid_record = Orcid.query.filter_by(orcid_id=orcid_id).first()

            if orcid_record:
                profile = UserProfile.query.get(orcid_record.profile_id)
                user = User.query.get(profile.user_id) if profile else None

                if user:
                    return user

                # Enlace roto: limpiamos y reconstruimos
                if not profile or not user:
                    db.session.delete(orcid_record)
                    db.session.flush()  # no commit aún, seguimos para recrear

            # 2) Crear usuario + perfil + enlace ORCID
            user = User(
                # puedes guardar email si algún día lo pides a ORCID con más scope
                password=generate_password_hash(secrets.token_urlsafe(24)),
                active=True,
            )
            db.session.add(user)
            db.session.flush()  # para obtener user.id

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
            return user

        except SQLAlchemyError as e:
            current_app.logger.exception("Error creando usuario ORCID: %s", e)
            db.session.rollback()
            return None
