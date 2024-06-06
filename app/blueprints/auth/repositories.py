import app
from app.blueprints.auth.models import User
from core.repositories.BaseRepository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User)

    def create(self, **kwargs):
        password = kwargs.pop("password")
        instance = self.model(**kwargs)
        instance.set_password(password)
        app.db.session.add(instance)
        app.db.session.commit()
        return instance

    def get_by_email(self, email: str):
        return self.model.query.filter_by(email=email).first()
