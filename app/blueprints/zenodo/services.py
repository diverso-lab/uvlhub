from app.blueprints.zenodo.repositories import ZenodoRepository
from app.services.BaseService import BaseService


class Zenodo(BaseService):
    def __init__(self):
        super().__init__(ZenodoRepository())
