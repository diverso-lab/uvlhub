from datetime import datetime

import pytz
from flask import abort, current_app, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from splent_framework.services.BaseService import BaseService

from app.features.auth.repositories import UserRepository
from app.features.reset.repositories import ResetRepository
from app.managers.task_queue_manager import TaskQueueManager

RESET_SALT = "email-confirm"
TOKEN_MAX_AGE_SECONDS = 3600


class ResetService(BaseService):
    def __init__(self):
        super().__init__(ResetRepository())
        self.user_repository = UserRepository()

    def get_serializer(self) -> URLSafeTimedSerializer:
        return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

    def send_reset_password_mail(self, email: str) -> str | None:
        user = self.user_repository.get_by_email(email, active=None)
        if not user:
            return None

        token = self.get_serializer().dumps(email, salt=RESET_SALT)
        link = url_for("reset.reset_password", token=token, _external=True)
        TaskQueueManager().enqueue_task(
            "app.features.reset.tasks.send_reset_password_email", email=email, link=link, timeout=10
        )
        return token

    def reset_and_notify(self, email: str, password: str, token: str) -> None:
        """Reset the password, burn the token, and enqueue the confirmation email."""
        self.reset_password(email=email, password=password)
        self.mark_token_as_used(token)
        TaskQueueManager().enqueue_task(
            "app.features.reset.tasks.send_reset_confirmation_email", email=email, timeout=10
        )

    def add_token(self, token: str) -> None:
        if token is None or self.repository.get_by_token(token):
            return
        self.repository.create(token=token)

    def get_email_by_token(self, token: str) -> str:
        return self.get_serializer().loads(token, salt=RESET_SALT, max_age=TOKEN_MAX_AGE_SECONDS)

    def check_valid_token(self, token: str) -> None:
        try:
            self.get_serializer().loads(token, salt=RESET_SALT, max_age=TOKEN_MAX_AGE_SECONDS)
        except (SignatureExpired, BadSignature):
            abort(404)

    def token_already_used(self, token: str) -> bool:
        reset_token = self.repository.get_by_token(token)
        return bool(reset_token and reset_token.used_at)

    def reset_password(self, email: str, password: str) -> None:
        user = self.user_repository.get_by_email(email, active=None)
        if not user:
            raise ValueError(f"No account is associated with {email}.")
        user.set_password(password)
        self.user_repository.session.commit()

    def mark_token_as_used(self, token: str) -> None:
        reset_token = self.repository.get_by_token(token)
        if reset_token:
            self.repository.update(reset_token.id, used_at=datetime.now(pytz.utc))
