from app import db


class Downloadqueue(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return f"Downloadqueue<{self.id}>"
