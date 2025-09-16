import os

from dotenv import load_dotenv
from flask import current_app, url_for
from itsdangerous import BadTimeSignature, SignatureExpired, URLSafeTimedSerializer

from app import mail_service
from app.modules.auth.services import AuthenticationService
from app.modules.confirmemail.repositories import ConfirmemailRepository
from core.services.BaseService import BaseService

# Load environment variables
load_dotenv()

authentication_service = AuthenticationService()


class ConfirmemailService(BaseService):
    def __init__(self):
        super().__init__(ConfirmemailRepository())
        self.repository = ConfirmemailRepository()
        self.CONFIRM_EMAIL_SALT = os.getenv("CONFIRM_EMAIL_SALT", "sample_salt")
        self.CONFIRM_EMAIL_TOKEN_MAX_AGE = os.getenv("CONFIRM_EMAIL_TOKEN_MAX_AGE", 3600)

    def get_serializer(self):
        return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

    def get_token_from_email(self, email):
        s = self.get_serializer()
        return s.dumps(email, salt=self.CONFIRM_EMAIL_SALT)

    def send_confirmation_email(self, user_email):
        token = self.get_token_from_email(user_email)
        url = url_for("confirmemail.confirm_user", token=token, _external=True)

        html_body = f"<a href='{url}'>Please confirm your email</a>"

        mail_service.send_email(
            "Please confirm your email",
            recipients=[user_email],
            body="Please confirm your email by clicking the link below.",
            html_body=html_body,
        )

    def confirm_user_with_token(self, token):
        s = self.get_serializer()
        try:
            email = s.loads(
                token,
                salt=self.CONFIRM_EMAIL_SALT,
                max_age=self.CONFIRM_EMAIL_TOKEN_MAX_AGE,
            )
        except SignatureExpired:
            raise Exception("The confirmation link has expired.")
        except BadTimeSignature:
            raise Exception("The confirmation link has been tampered with.")

        user = authentication_service.get_by_email(email, active=False)
        user.active = True
        self.repository.session.commit()
        return user
