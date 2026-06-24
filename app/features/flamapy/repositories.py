from app.features.flamapy.models import Flamapy
from splent_framework.repositories.BaseRepository import BaseRepository


class FlamapyRepository(BaseRepository):
    def __init__(self):
        super().__init__(Flamapy)
