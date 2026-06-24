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

    @property
    def scope_list(self) -> list[str]:
        return [scope for scope in self.scopes.split(",") if scope]

    def __repr__(self) -> str:
        return f"<ApiKey {self.id} user={self.user_id}>"
