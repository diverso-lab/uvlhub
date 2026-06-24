from splent_framework.repositories.BaseRepository import BaseRepository

from app.features.dataset.models import DSDownloadRecord, DSViewRecord
from app.features.hubfile.models import HubfileDownloadRecord, HubfileViewRecord
from app.features.statistics.models import Statistics


class StatisticsRepository(BaseRepository):
    def __init__(self):
        super().__init__(Statistics)

    def get_statistics(self) -> Statistics:
        statistics = self.model.query.first()
        if statistics is None:
            # If no registry exists, create a new registry with default values
            statistics = Statistics(
                datasets_counter=0,
                feature_models_counter=0,
                datasets_viewed=0,
                feature_models_viewed=0,
                datasets_downloaded=0,
                feature_models_downloaded=0,
            )
            self.session.add(statistics)
            self.session.commit()
        return statistics

    # Incremental methods
    def increment_datasets_viewed(self) -> int:
        return self._increment_field("datasets_viewed")

    def increment_feature_models_viewed(self) -> int:
        return self._increment_field("feature_models_viewed")

    def increment_datasets_downloaded(self) -> int:
        return self._increment_field("datasets_downloaded")

    def increment_feature_models_downloaded(self) -> int:
        return self._increment_field("feature_models_downloaded")

    def _increment_field(self, field_name: str) -> int:
        statistics = self.get_statistics()
        current_value = getattr(statistics, field_name)
        new_value = current_value + 1
        setattr(statistics, field_name, new_value)
        self.session.commit()
        return new_value

    # Consultation methods
    def get_datasets_viewed(self) -> int:
        statistics = self.get_statistics()
        return statistics.datasets_viewed

    def get_feature_models_viewed(self) -> int:
        statistics = self.get_statistics()
        return statistics.feature_models_viewed

    def get_datasets_downloaded(self) -> int:
        statistics = self.get_statistics()
        return statistics.datasets_downloaded

    def get_feature_models_downloaded(self) -> int:
        statistics = self.get_statistics()
        return statistics.feature_models_downloaded

    def compute_totals(self) -> dict[str, int]:
        """Re-compute every counter from the record tables without touching
        the persisted row. Every total is restricted to datasets with a DOI
        so the counters line up with what the `/statistics` dashboard shows.
        """
        from app.features.dataset.models import DataSet, DSMetaData
        from app.features.featuremodel.models import FeatureModel

        synchronized_dataset_ids = (
            self.session.query(DataSet.id).join(DSMetaData).filter(DSMetaData.dataset_doi.isnot(None)).scalar_subquery()
        )
        synchronized_featuremodel_ids = (
            self.session.query(FeatureModel.id)
            .filter(FeatureModel.dataset_id.in_(synchronized_dataset_ids))
            .scalar_subquery()
        )
        from app.features.hubfile.models import Hubfile

        synchronized_hubfile_ids = (
            self.session.query(Hubfile.id)
            .filter(Hubfile.feature_model_id.in_(synchronized_featuremodel_ids))
            .scalar_subquery()
        )

        return {
            "datasets_counter": (
                self.session.query(DataSet).join(DSMetaData).filter(DSMetaData.dataset_doi.isnot(None)).count()
            ),
            "feature_models_counter": (
                self.session.query(FeatureModel).filter(FeatureModel.dataset_id.in_(synchronized_dataset_ids)).count()
            ),
            "datasets_viewed": (
                self.session.query(DSViewRecord).filter(DSViewRecord.dataset_id.in_(synchronized_dataset_ids)).count()
            ),
            "datasets_downloaded": (
                self.session.query(DSDownloadRecord)
                .filter(DSDownloadRecord.dataset_id.in_(synchronized_dataset_ids))
                .count()
            ),
            "feature_models_viewed": (
                self.session.query(HubfileViewRecord)
                .filter(HubfileViewRecord.file_id.in_(synchronized_hubfile_ids))
                .count()
            ),
            "feature_models_downloaded": (
                self.session.query(HubfileDownloadRecord)
                .filter(HubfileDownloadRecord.file_id.in_(synchronized_hubfile_ids))
                .count()
            ),
        }

    def refresh_statistics(self) -> Statistics:
        """Persist the recomputed totals into the singleton row."""
        statistics = self.get_statistics()
        for field, value in self.compute_totals().items():
            setattr(statistics, field, value)
        self.session.commit()
        return statistics
