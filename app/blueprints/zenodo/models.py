from app import db


class Zenodo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
