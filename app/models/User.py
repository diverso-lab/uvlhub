from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    data_sets = db.relationship('DataSet', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'
