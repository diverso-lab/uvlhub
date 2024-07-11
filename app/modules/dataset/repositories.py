from datetime import datetime, timezone
import logging
import re
from flask_login import current_user
import unidecode
from typing import Optional

from sqlalchemy import desc, func, or_, any_

from app.modules.dataset.models import (
    Author,
    DOIMapping,
    DSDownloadRecord,
    DSMetaData,
    DSViewRecord,
    DataSet,
    FMMetaData,
    FeatureModel,
    PublicationType,
)
from core.repositories.BaseRepository import BaseRepository

logger = logging.getLogger(__name__)


class AuthorRepository(BaseRepository):
    def __init__(self):
        super().__init__(Author)


class DSDownloadRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(DSDownloadRecord)

    def total_dataset_downloads(self) -> int:
        max_id = self.model.query.with_entities(func.max(self.model.id)).scalar()
        return max_id if max_id is not None else 0


class DSMetaDataRepository(BaseRepository):
    def __init__(self):
        super().__init__(DSMetaData)

    def filter_by_doi(self, doi: str) -> Optional[DSMetaData]:
        return self.model.query.filter_by(dataset_doi=doi).first()


class DSViewRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(DSViewRecord)

    def total_dataset_views(self) -> int:
        max_id = self.model.query.with_entities(func.max(self.model.id)).scalar()
        return max_id if max_id is not None else 0

    def the_record_exists(self, dataset: DataSet, user_cookie: str):
        return self.model.query.filter_by(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset.id,
            view_cookie=user_cookie
        ).first()

    def create_new_record(self, dataset: DataSet, user_cookie: str) -> DSViewRecord:
        return self.create(
                user_id=current_user.id if current_user.is_authenticated else None,
                dataset_id=dataset.id,
                view_date=datetime.now(timezone.utc),
                view_cookie=user_cookie,
            )


class DataSetRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

    def get_synchronized(self, current_user_id: int) -> DataSet:
        return (
            self.model.query.join(DSMetaData)
            .filter(DataSet.user_id == current_user_id, DSMetaData.dataset_doi.isnot(None))
            .order_by(self.model.created_at.desc())
            .all()
        )

    def get_unsynchronized(self, current_user_id: int) -> DataSet:
        return (
            self.model.query.join(DSMetaData)
            .filter(DataSet.user_id == current_user_id, DSMetaData.dataset_doi.is_(None))
            .order_by(self.model.created_at.desc())
            .all()
        )

    def get_unsynchronized_dataset(self, current_user_id: int, dataset_id: int) -> DataSet:
        return (
            self.model.query.join(DSMetaData)
            .filter(DataSet.user_id == current_user_id, DataSet.id == dataset_id, DSMetaData.dataset_doi.is_(None))
            .first()
        )

    def filter(self, query="", sorting="newest", publication_type="any", tags=[], **kwargs):
        # Normalize and remove unwanted characters
        normalized_query = unidecode.unidecode(query).lower()
        cleaned_query = re.sub(r'[,.":\'()\[\]^;!¡¿?]', "", normalized_query)
        logger.info(f"Cleaned query: {cleaned_query}")

        filters = []
        for word in cleaned_query.split():
            filters.append(DSMetaData.title.ilike(f"%{word}%"))
            filters.append(DSMetaData.description.ilike(f"%{word}%"))
            filters.append(Author.name.ilike(f"%{word}%"))
            filters.append(Author.affiliation.ilike(f"%{word}%"))
            filters.append(Author.orcid.ilike(f"%{word}%"))
            filters.append(FMMetaData.uvl_filename.ilike(f"%{word}%"))
            filters.append(FMMetaData.title.ilike(f"%{word}%"))
            filters.append(FMMetaData.description.ilike(f"%{word}%"))
            filters.append(FMMetaData.publication_doi.ilike(f"%{word}%"))
            filters.append(FMMetaData.tags.ilike(f"%{word}%"))
            filters.append(DSMetaData.tags.ilike(f"%{word}%"))

        datasets = (
            self.model.query
            .join(DataSet.ds_meta_data)
            .join(DSMetaData.authors)
            .join(DataSet.feature_models)
            .join(FeatureModel.fm_meta_data)
            .filter(or_(*filters))
        )
        logger.info(f"Found datasets with {cleaned_query}: {datasets.all()}")

        if publication_type != "any":
            matching_type = None
            for member in PublicationType:
                if member.value.lower() == publication_type:
                    matching_type = member
                    break

            if matching_type is not None:
                datasets = datasets.filter(DSMetaData.publication_type == matching_type.name)

        if tags:
            datasets = datasets.filter(DSMetaData.tags.ilike(any_(f"%{tag}%" for tag in tags)))

        # Order by created_at
        if sorting == "oldest":
            datasets = datasets.order_by(self.model.created_at.asc())
        else:
            datasets = datasets.order_by(self.model.created_at.desc())

        return datasets.all()

    def count_synchronized_datasets(self):
        return (
            self.model.query.join(DSMetaData)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .count()
        )

    def count_unsynchronized_datasets(self):
        return (
            self.model.query.join(DSMetaData)
            .filter(DSMetaData.dataset_doi.is_(None))
            .count()
        )

    def latest_synchronized(self):
        return (
            self.model.query.join(DSMetaData)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .order_by(desc(self.model.id))
            .limit(5)
            .all()
        )


class FMMetaDataRepository(BaseRepository):
    def __init__(self):
        super().__init__(FMMetaData)


class FeatureModelRepository(BaseRepository):
    def __init__(self):
        super().__init__(FeatureModel)

    def count_feature_models(self) -> int:
        max_id = self.model.query.with_entities(func.max(self.model.id)).scalar()
        return max_id if max_id is not None else 0


class DOIMappingRepository(BaseRepository):
    def __init__(self):
        super().__init__(DOIMapping)

    def get_new_doi(self, old_doi: str) -> str:
        return self.model.query.filter_by(dataset_doi_old=old_doi).first()
