from app.features.downloadqueue.repositories import DownloadqueueRepository
from splent_framework.services.BaseService import BaseService


class DownloadqueueService(BaseService):
    def __init__(self):
        super().__init__(DownloadqueueRepository())
