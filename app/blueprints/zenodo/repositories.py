from app.blueprints.zenodo.models import Zenodo
from app.repositories.BaseRepository import BaseRepository


class ZenodoRepository(BaseRepository):
    def __init__(self):
        super().__init__(Zenodo)
