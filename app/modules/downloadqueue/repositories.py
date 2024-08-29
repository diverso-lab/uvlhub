from app.modules.downloadqueue.models import Downloadqueue
from core.repositories.BaseRepository import BaseRepository


class DownloadqueueRepository(BaseRepository):
    def __init__(self):
        super().__init__(Downloadqueue)
