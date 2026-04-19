from app.modules.generator.models import Generator
from core.repositories.BaseRepository import BaseRepository


class GeneratorRepository(BaseRepository):
    def __init__(self):
        super().__init__(Generator)
