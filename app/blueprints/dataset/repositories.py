from typing import Optional

from app.blueprints.dataset.models import (
    Author,
    DSDownloadRecord,
    DSMetaData,
    DSViewRecord,
    DataSet,
    FMMetaData,
    FeatureModel,
    File,
    FileDownloadRecord,
)
from core.repositories.BaseRepository import BaseRepository


class AuthorRepository(BaseRepository):
    def __init__(self):
        super().__init__(Author)


class DSDownloadRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(DSDownloadRecord)


class DSMetaDataRepository(BaseRepository):
    def __init__(self):
        super().__init__(DSMetaData)

    def filter_by_doi(self, doi: str) -> Optional[DSMetaData]:
        return self.model.query.filter_by(dataset_doi=doi).first()


class DSViewRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(DSViewRecord)


class DataSetRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

    def get_synchronized(self, current_user_id: int) -> DataSet:
        return (
            self.model.query.join(DSMetaData)
            .filter(
                DataSet.user_id == current_user_id, DSMetaData.dataset_doi.isnot(None)
            )
            .order_by(DataSet.created_at.desc())
            .all()
        )

    def get_unsynchronized(self, current_user_id: int) -> DataSet:
        return (
            self.model.query.join(DSMetaData)
            .filter(
                DataSet.user_id == current_user_id, DSMetaData.dataset_doi.is_(None)
            )
            .order_by(DataSet.created_at.desc())
            .all()
        )


class FMMetaDataRepository(BaseRepository):
    def __init__(self):
        super().__init__(FMMetaData)


class FeatureModelRepository(BaseRepository):
    def __init__(self):
        super().__init__(FeatureModel)


class FileRepository(BaseRepository):
    def __init__(self):
        super().__init__(File)


class FileDownloadRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(FileDownloadRecord)
