from app import db


class UserProfile(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)

    affiliation = db.Column(db.String(100))
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)

    orcid = db.relationship("Orcid", backref="profile", uselist=False)

    def get_orcid(self):
        return self.orcid.orcid_id if self.orcid else None
