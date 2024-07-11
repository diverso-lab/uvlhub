from sqlalchemy import func
from app.modules.hubfile.models import Hubfile, HubfileDownloadRecord, HubfileViewRecord
from core.repositories.BaseRepository import BaseRepository


class HubfileRepository(BaseRepository):
    def __init__(self):
        super().__init__(Hubfile)


class HubfileDownloadRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(HubfileDownloadRecord)

    def total_feature_model_downloads(self) -> int:
        max_id = self.model.query.with_entities(func.max(self.model.id)).scalar()
        return max_id if max_id is not None else 0


class HubfileViewRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(HubfileViewRecord)

    def total_feature_model_views(self) -> int:
        max_id = self.model.query.with_entities(func.max(self.model.id)).scalar()
        return max_id if max_id is not None else 0