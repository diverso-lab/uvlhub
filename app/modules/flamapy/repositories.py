from app.modules.flamapy.models import Flamapy
from core.repositories.BaseRepository import BaseRepository


class FlamapyRepository(BaseRepository):
    def __init__(self):
        super().__init__(Flamapy)
