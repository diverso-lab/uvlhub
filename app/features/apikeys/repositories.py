from app.features.apikeys.models import Apikeys
from splent_framework.repositories.BaseRepository import BaseRepository


class ApikeysRepository(BaseRepository):
    def __init__(self):
        super().__init__(Apikeys)
