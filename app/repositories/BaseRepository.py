from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class BaseRepository:
    def __init__(self, model):
        self.model = model

    def create(self, **kwargs):
        instance = self.model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    def get_by_id(self, id):
        return self.model.query.get(id)

    def update(self, id, **kwargs):
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            db.session.commit()
            return instance
        return None

    def delete(self, id):
        instance = self.get_by_id(id)
        if instance:
            db.session.delete(instance)
            db.session.commit()
            return True
        return False
