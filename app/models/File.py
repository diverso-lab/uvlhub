from app import db


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    checksum = db.Column(db.String(120), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    data_set_id = db.Column(db.Integer, db.ForeignKey('data_set.id'), nullable=False)

    def __repr__(self):
        return f'File<{self.name}>'
