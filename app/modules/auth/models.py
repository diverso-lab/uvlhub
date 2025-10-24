from datetime import datetime

import pytz
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(256), unique=True, nullable=True)
    password = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.utc))

    data_sets = db.relationship("DataSet", backref="user", lazy=True)
    profile = db.relationship("UserProfile", backref="user", uselist=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    api_keys = db.relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if "password" in kwargs:
            self.set_password(kwargs["password"])

    def __repr__(self):
        return f"<User {self.email}>"

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def temp_folder(self) -> str:
        from app.modules.auth.services import AuthenticationService

        return AuthenticationService().temp_folder_by_user(self)
