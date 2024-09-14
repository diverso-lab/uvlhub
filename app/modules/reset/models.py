from app import db


class ResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(256), unique=True, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"Reset<{self.id}>"
