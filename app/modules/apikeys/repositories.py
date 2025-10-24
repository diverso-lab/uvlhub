from app.modules.apikeys.models import Apikeys
from core.repositories.BaseRepository import BaseRepository


class ApikeysRepository(BaseRepository):
    def __init__(self):
        super().__init__(Apikeys)
