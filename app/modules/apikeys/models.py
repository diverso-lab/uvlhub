# app/modules/apikeys/models.py

import secrets
from datetime import datetime

from app import db


class ApiKey(db.Model):
    __tablename__ = "api_keys"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    scopes = db.Column(db.String(256), nullable=False)  # comma-separated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime)

    user = db.relationship("User", back_populates="api_keys")

    @staticmethod
    def generate(user, scopes: list[str]):
        token = secrets.token_hex(32)
        api_key = ApiKey(key=token, user=user, scopes=",".join(scopes))
        db.session.add(api_key)
        db.session.commit()
        return api_key, token
