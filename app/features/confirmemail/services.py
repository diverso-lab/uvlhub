import os

from flask import current_app, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app import mail_service
from app.features.auth.services import AuthenticationService

DEFAULT_TOKEN_MAX_AGE_SECONDS = 3600


class EmailConfirmationError(Exception):
    """Raised when a confirmation token is invalid, tampered with or expired."""


class ConfirmemailService:
    """Stateless service: confirmation is a token operation over the User domain.

    It owns no persistent entity of its own, so it delegates user activation to
    the auth feature instead of carrying a repository.
    """

    def __init__(self):
        self.authentication_service = AuthenticationService()
        self.CONFIRM_EMAIL_SALT = os.getenv("CONFIRM_EMAIL_SALT", "sample_salt")
        self.CONFIRM_EMAIL_TOKEN_MAX_AGE = int(os.getenv("CONFIRM_EMAIL_TOKEN_MAX_AGE", DEFAULT_TOKEN_MAX_AGE_SECONDS))

    def get_serializer(self) -> URLSafeTimedSerializer:
        return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

    def get_token_from_email(self, email: str) -> str:
        return self.get_serializer().dumps(email, salt=self.CONFIRM_EMAIL_SALT)

    def send_confirmation_email(self, user_email: str) -> None:
        token = self.get_token_from_email(user_email)
        url = url_for("confirmemail.confirm_user", token=token, _external=True)
        html_body = f"<a href='{url}'>Please confirm your email</a>"

        mail_service.send_email(
            "Please confirm your email",
            recipients=[user_email],
            body="Please confirm your email by clicking the link below.",
            html_body=html_body,
        )

    def confirm_user_with_token(self, token: str):
        try:
            email = self.get_serializer().loads(
                token, salt=self.CONFIRM_EMAIL_SALT, max_age=self.CONFIRM_EMAIL_TOKEN_MAX_AGE
            )
        except SignatureExpired:
            raise EmailConfirmationError("The confirmation link has expired.")
        except BadSignature:
            raise EmailConfirmationError("The confirmation link is invalid.")

        return self.authentication_service.activate_user(email)
