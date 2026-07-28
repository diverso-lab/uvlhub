import logging
from datetime import datetime
from typing import List, Optional

import pytz
from flask_login import current_user
from splent_framework.repositories.BaseRepository import BaseRepository
from sqlalchemy import desc

from app.features.dataset.models import (
    Author,
    DataSet,
    DatasetTransferRequest,
    DatasetTransferStatus,
    DOIMapping,
    DSDownloadRecord,
    DSMetaData,
    DSViewRecord,
)

logger = logging.getLogger(__name__)


class AuthorRepository(BaseRepository):
    def __init__(self):
        super().__init__(Author)


class DatasetTransferRequestRepository(BaseRepository):
    def __init__(self):
        super().__init__(DatasetTransferRequest)

    def get_pending_for_dataset(self, dataset_id: int) -> Optional[DatasetTransferRequest]:
        return self.model.query.filter_by(dataset_id=dataset_id, status=DatasetTransferStatus.PENDING).first()

    def get_pending_for_datasets(self, dataset_ids: List[int]) -> List[DatasetTransferRequest]:
        """Any pending offer touching one of these datasets.

        A transfer moves a whole lineage, so an offer on any of its members
        blocks a second offer on any other member.
        """
        if not dataset_ids:
            return []
        return (
            self.model.query.filter(
                self.model.dataset_id.in_(dataset_ids),
                self.model.status == DatasetTransferStatus.PENDING,
            )
            .order_by(self.model.id.asc())
            .all()
        )

    def get_involving_user(self, user_id: int, status: Optional[DatasetTransferStatus] = None):
        query = self.model.query.filter((self.model.from_user_id == user_id) | (self.model.to_user_id == user_id))
        if status is not None:
            query = query.filter(self.model.status == status)
        return query.order_by(self.model.id.desc()).all()


class DSDownloadRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(DSDownloadRecord)

    def the_record_exists(self, dataset: DataSet, user_cookie: str):
        return self.model.query.filter_by(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset.id,
            download_cookie=user_cookie,
        ).first()

    def create_new_record(self, dataset: DataSet, user_cookie: str) -> DSDownloadRecord:
        return self.create(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset.id,
            download_date=datetime.now(pytz.utc),
            download_cookie=user_cookie,
        )


class DSMetaDataRepository(BaseRepository):
    def __init__(self):
        super().__init__(DSMetaData)

    def filter_by_doi(self, doi: str) -> Optional[DSMetaData]:
        return self.model.query.filter_by(dataset_doi=doi).first()


class DSViewRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(DSViewRecord)

    def the_record_exists(self, dataset: DataSet, user_cookie: str):
        return self.model.query.filter_by(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset.id,
            view_cookie=user_cookie,
        ).first()

    def create_new_record(self, dataset: DataSet, user_cookie: str) -> DSViewRecord:
        return self.create(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset.id,
            view_date=datetime.now(pytz.utc),
            view_cookie=user_cookie,
        )


class DataSetRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

    def is_synchronized(self, dataset_id: int) -> bool:
        dataset = self.model.query.join(DSMetaData).filter(self.model.id == dataset_id).first()
        if dataset and dataset.ds_meta_data.dataset_doi:
            return True
        return False

    def get_by_concept_doi(self, concept_doi: str) -> Optional[DataSet]:
        """Any dataset carrying this concept DOI, oldest version first.

        One member is enough to walk the lineage, and taking the oldest keeps
        the answer stable when only some versions store the value.
        """
        if not concept_doi:
            return None
        return (
            self.model.query.join(DSMetaData)
            .filter(DSMetaData.dataset_concept_doi == concept_doi)
            .order_by(self.model.dataset_version.asc(), self.model.id.asc())
            .first()
        )

    def _exclude_superseded(self, query):
        """Keep only the latest version of each lineage.

        A dataset is superseded when a newer version points at it via
        dataset_origin_id, so we drop every id that appears as some other
        dataset's origin.
        """
        superseded = self.model.query.with_entities(DataSet.dataset_origin_id).filter(
            DataSet.dataset_origin_id.isnot(None)
        )
        return query.filter(DataSet.id.notin_(superseded))

    """
        Synchronised dataset
    """

    def get_synchronized_datasets(self) -> List[DataSet]:
        return (
            self.model.query.join(DSMetaData)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .order_by(self.model.created_at.desc())
            .all()
        )

    def get_synchronized_datasets_by_user(self, current_user_id: int) -> List[DataSet]:
        query = self.model.query.join(DSMetaData).filter(
            DataSet.user_id == current_user_id, DSMetaData.dataset_doi.isnot(None)
        )
        return self._exclude_superseded(query).order_by(self.model.created_at.desc()).all()

    def get_synchronized_dataset_by_user(self, current_user_id: int, dataset_id: int) -> DataSet:
        return (
            self.model.query.join(DSMetaData)
            .filter(
                DataSet.user_id == current_user_id,
                DataSet.id == dataset_id,
                DSMetaData.dataset_doi.isnot(None),
            )
            .first()
        )

    def count_synchronized_datasets(self) -> int:
        return self.model.query.join(DSMetaData).filter(DSMetaData.dataset_doi.isnot(None)).count()

    """
        Unsynchronised dataset
    """

    def get_unsynchronized_datasets(self) -> List[DataSet]:
        return (
            self.model.query.join(DSMetaData)
            .filter(DSMetaData.dataset_doi.is_(None))
            .order_by(self.model.created_at.desc())
            .all()
        )

    def get_unsynchronized_datasets_by_user(self, current_user_id: int) -> List[DataSet]:
        query = self.model.query.join(DSMetaData).filter(
            DataSet.user_id == current_user_id, DSMetaData.dataset_doi.is_(None)
        )
        return self._exclude_superseded(query).order_by(self.model.created_at.desc()).all()

    def get_unsynchronized_dataset_by_user(self, current_user_id: int, dataset_id: int) -> DataSet:
        return (
            self.model.query.join(DSMetaData)
            .filter(
                DataSet.user_id == current_user_id,
                DataSet.id == dataset_id,
                DSMetaData.dataset_doi.is_(None),
            )
            .first()
        )

    def count_unsynchronized_datasets(self):
        return self.model.query.join(DSMetaData).filter(DSMetaData.dataset_doi.is_(None)).count()

    """
        Top X datasets...
    """

    def latest_synchronized(self) -> List[DataSet]:
        return (
            self.model.query.join(DSMetaData)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .order_by(desc(self.model.id))
            .limit(5)
            .all()
        )

    def get_top_5_datasets_by_feature_model_count(self) -> List[DataSet]:
        return (
            self.model.query.join(DSMetaData)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .order_by(self.model.feature_model_count.desc())
            .order_by(desc(self.model.created_at))
            .limit(5)
            .all()
        )


class DOIMappingRepository(BaseRepository):
    def __init__(self):
        super().__init__(DOIMapping)

    def get_new_doi(self, old_doi: str) -> str:
        return self.model.query.filter_by(dataset_doi_old=old_doi).first()
