from datetime import datetime

import pytz
from flask import abort, current_app, url_for
from itsdangerous import BadTimeSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import generate_password_hash

from app import db
from app.features.auth.models import User
from app.features.reset.models import ResetToken
from app.features.reset.repositories import ResetRepository
from app.managers.task_queue_manager import TaskQueueManager
from splent_framework.services.BaseService import BaseService


class ResetService(BaseService):
    def __init__(self):
        super().__init__(ResetRepository())

    def get_serializer(self):
        return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

    def send_reset_password_mail(self, email: str) -> str:
        token = None

        user = User.query.filter_by(email=email).first()
        if user:
            s = self.get_serializer()
            token = s.dumps(email, salt="email-confirm")
            link = url_for("reset.reset_password", token=token, _external=True)

            # 🧩 Encolar tarea en vez de enviar directamente
            task_manager = TaskQueueManager()
            task_manager.enqueue_task(
                "app.features.reset.tasks.send_reset_password_email",
                email=email,
                link=link,
                timeout=10,
            )

        return token

    def reset_and_notify(self, email: str, password: str, token: str):
        """Reset the password, mark the token as used, and enqueue the background notification."""
        self.reset_password(email=email, password=password)
        self.mark_token_as_used(token)

        task_manager = TaskQueueManager()
        task_manager.enqueue_task(
            "app.features.reset.tasks.send_reset_confirmation_email",
            email=email,
            timeout=10,
        )

    def add_token(self, token: str):
        if token is None:
            return

        existing = ResetToken.query.filter_by(token=token).first()
        if existing:
            return

        reset_token = ResetToken(token=token)
        db.session.add(reset_token)
        db.session.commit()

    def get_email_by_token(self, token: str) -> str:
        s = self.get_serializer()
        email = s.loads(token, salt="email-confirm", max_age=3600)
        return email

    def check_valid_token(self, token: str):
        s = self.get_serializer()
        try:
            s.loads(token, salt="email-confirm", max_age=3600)
        except SignatureExpired:
            abort(404)
        except BadTimeSignature:
            abort(404)

    def token_already_used(self, token: str) -> bool:
        reset_token = ResetToken.query.filter_by(token=token).first()
        return reset_token and reset_token.used_at

    def reset_password(self, email: str, password: str):
        hashed_password = generate_password_hash(password)
        user = User.query.filter_by(email=email).first()
        user.password = hashed_password
        db.session.commit()

    def mark_token_as_used(self, token: str):
        reset_token = ResetToken.query.filter_by(token=token).first()
        reset_token.used_at = datetime.now(pytz.utc)
        db.session.add(reset_token)
        db.session.commit()
