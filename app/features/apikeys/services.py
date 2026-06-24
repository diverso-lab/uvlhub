from app.features.apikeys.repositories import ApikeysRepository
from splent_framework.services.BaseService import BaseService


class ApikeysService(BaseService):
    def __init__(self):
        super().__init__(ApikeysRepository())
