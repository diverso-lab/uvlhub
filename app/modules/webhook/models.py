from app import db


class Webhook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
