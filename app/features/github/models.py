from datetime import datetime

import pytz

from app import db


class Github(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    github_id = db.Column(db.Integer, unique=True, nullable=False)
    github_login = db.Column(db.String(255), nullable=False)
    registration_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.utc))
    profile_id = db.Column(db.Integer, db.ForeignKey("user_profile.id"), unique=True)

    def __repr__(self):
        return f"Github<{self.github_login}>"
