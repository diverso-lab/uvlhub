import secrets
from datetime import datetime

import pytz
from splent_framework.services.BaseService import BaseService

from app.features.apikeys.models import ApiKey
from app.features.apikeys.repositories import ApiKeyRepository

TOKEN_BYTES = 32


class ApiKeyService(BaseService):
    def __init__(self):
        super().__init__(ApiKeyRepository())

    def generate_for_user(self, user, scopes: list[str]) -> tuple[ApiKey, str]:
        token = secrets.token_hex(TOKEN_BYTES)
        api_key = self.repository.create(key=token, user_id=user.id, scopes=",".join(scopes))
        return api_key, token

    def list_for_user(self, user) -> list[ApiKey]:
        return self.repository.list_for_user(user.id)

    def delete_for_user(self, key_id, user) -> bool:
        api_key = self.repository.get_for_user(key_id, user.id)
        if api_key is None:
            return False
        self.repository.delete(api_key.id)
        return True

    def get_valid_key(self, key: str) -> ApiKey | None:
        return self.repository.get_by_key(key)

    def mark_used(self, api_key: ApiKey) -> ApiKey | None:
        return self.repository.update(api_key.id, last_used_at=datetime.now(pytz.utc))
