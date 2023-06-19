from app import db


class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    orcid = db.Column(db.String(19))
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()