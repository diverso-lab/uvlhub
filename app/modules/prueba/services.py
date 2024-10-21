from app.modules.prueba.repositories import PruebaRepository
from core.services.BaseService import BaseService


class PruebaService(BaseService):
    def __init__(self):
        super().__init__(PruebaRepository())
