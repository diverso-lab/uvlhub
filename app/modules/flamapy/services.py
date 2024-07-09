from app.modules.flamapy.repositories import FlamapyRepository
from core.services.BaseService import BaseService


class FlamapyService(BaseService):
    def __init__(self):
        super().__init__(FlamapyRepository())
