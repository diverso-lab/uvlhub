from app import db


class Prueba(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return f'Prueba<{self.id}>'
