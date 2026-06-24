from app.features.downloadqueue.models import Downloadqueue
from splent_framework.repositories.BaseRepository import BaseRepository


class DownloadqueueRepository(BaseRepository):
    def __init__(self):
        super().__init__(Downloadqueue)
