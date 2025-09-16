from datetime import datetime

import pytz

from app import db


class Orcid(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    orcid_id = db.Column(db.String(19), unique=True, nullable=False)
    registration_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.utc))

    profile_id = db.Column(db.Integer, db.ForeignKey("user_profile.id"), unique=True)

    def __repr__(self):
        return f"Orcid<{self.orcid_id}>"
