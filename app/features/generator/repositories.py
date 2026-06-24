from app.features.generator.models import Generator
from splent_framework.repositories.BaseRepository import BaseRepository


class GeneratorRepository(BaseRepository):
    def __init__(self):
        super().__init__(Generator)
