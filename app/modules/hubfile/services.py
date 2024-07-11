from app.modules.hubfile.repositories import HubfileRepository
from core.services.BaseService import BaseService


class HubfileService(BaseService):
    def __init__(self):
        super().__init__(HubfileRepository())


class HubfileDownloadRecordService(BaseService):
    def __init__(self):
        super().__init__(FileDownloadRecordRepository())