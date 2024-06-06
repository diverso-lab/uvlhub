from app.blueprints.dataset.repositories import DataSetRepository
from core.services.BaseService import BaseService


class DataSetService(BaseService):
    def __init__(self):
        super().__init__(DataSetRepository())
