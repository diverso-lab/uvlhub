from app import db


class Confirmemail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
