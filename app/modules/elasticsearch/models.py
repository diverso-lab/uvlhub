from app import db


class Elasticsearch(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return f"Elasticsearch<{self.id}>"
