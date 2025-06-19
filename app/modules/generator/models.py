from app import db


class Generator(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return f'Generator<{self.id}>'
