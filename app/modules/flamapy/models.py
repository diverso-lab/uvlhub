from app import db


class Flamapy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
