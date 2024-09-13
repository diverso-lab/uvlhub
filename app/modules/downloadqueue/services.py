from app.modules.downloadqueue.repositories import DownloadqueueRepository
from core.services.BaseService import BaseService


class DownloadqueueService(BaseService):
    def __init__(self):
        super().__init__(DownloadqueueRepository())
