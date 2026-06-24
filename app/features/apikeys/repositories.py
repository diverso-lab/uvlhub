from splent_framework.repositories.BaseRepository import BaseRepository

from app.features.apikeys.models import ApiKey


class ApiKeyRepository(BaseRepository):
    def __init__(self):
        super().__init__(ApiKey)

    def get_by_key(self, key: str) -> ApiKey | None:
        return self.model.query.filter_by(key=key).first()

    def list_for_user(self, user_id: int) -> list[ApiKey]:
        return self.model.query.filter_by(user_id=user_id).order_by(ApiKey.created_at.desc()).all()

    def get_for_user(self, key_id, user_id: int) -> ApiKey | None:
        return self.model.query.filter_by(id=key_id, user_id=user_id).first()
