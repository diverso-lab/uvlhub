from app.modules.prueba.models import Prueba
from core.repositories.BaseRepository import BaseRepository


class PruebaRepository(BaseRepository):
    def __init__(self):
        super().__init__(Prueba)
