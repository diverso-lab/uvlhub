from splent_framework.repositories.BaseRepository import BaseRepository

from app.features.auth.models import ExternalIdentity, User


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User)

    def create(self, commit: bool = True, **kwargs):
        password = kwargs.pop("password")
        instance = self.model(**kwargs)
        instance.set_password(password)
        self.session.add(instance)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        return instance

    def get_by_email(self, email: str, active: bool | None = None):
        normalized_email = email.strip().lower()
        query = self.model.query.filter_by(email=normalized_email)
        if active is not None:
            query = query.filter_by(active=active)
        return query.first()


class ExternalIdentityRepository(BaseRepository):
    def __init__(self):
        super().__init__(ExternalIdentity)

    def get_by_provider_id(self, provider: str, provider_id: str):
        return self.session.query(ExternalIdentity).filter_by(provider=provider, provider_id=str(provider_id)).first()

    def get_all_by_user(self, user_id: int):
        return self.session.query(ExternalIdentity).filter_by(user_id=user_id).all()

    def get_by_email(self, email: str):
        if not email:
            return None
        return self.session.query(ExternalIdentity).filter_by(email=email).first()
