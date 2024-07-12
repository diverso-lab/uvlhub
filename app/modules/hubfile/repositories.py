from sqlalchemy import func
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet
from app.modules.featuremodel.models import FeatureModel
from app.modules.hubfile.models import Hubfile, HubfileDownloadRecord, HubfileViewRecord
from core.repositories.BaseRepository import BaseRepository
from app import db


class HubfileRepository(BaseRepository):
    def __init__(self):
        super().__init__(Hubfile)

    def get_owner_user_by_hubfile(self, hubfile: Hubfile) -> User:
        return (
            db.session.query(User)
            .join(DataSet)
            .join(FeatureModel)
            .join(Hubfile)
            .filter(Hubfile.id == hubfile.id)
            .first()
        )

    def get_dataset_by_hubfile(self, hubfile: Hubfile) -> DataSet:
        return db.session.query(DataSet).join(FeatureModel).join(Hubfile).filter(Hubfile.id == hubfile.id).first()


class HubfileViewRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(HubfileViewRecord)

    def total_hubfile_views(self) -> int:
        max_id = self.model.query.with_entities(func.max(self.model.id)).scalar()
        return max_id if max_id is not None else 0


class HubfileDownloadRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(HubfileDownloadRecord)

    def total_hubfile_downloads(self) -> int:
        max_id = self.model.query.with_entities(func.max(self.model.id)).scalar()
        return max_id if max_id is not None else 0
