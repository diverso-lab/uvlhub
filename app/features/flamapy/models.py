from app import db


class Flamapy(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return f"Flamapy<{self.id}>"
