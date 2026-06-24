from app.features.explore.repositories import ExploreRepository
from splent_framework.services.BaseService import BaseService


class ExploreService(BaseService):
    def __init__(self):
        super().__init__(ExploreRepository())
