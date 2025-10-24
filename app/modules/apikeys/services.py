from app.modules.apikeys.repositories import ApikeysRepository
from core.services.BaseService import BaseService


class ApikeysService(BaseService):
    def __init__(self):
        super().__init__(ApikeysRepository())
