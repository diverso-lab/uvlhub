from app.modules.statistics.models import Statistics
from core.repositories.BaseRepository import BaseRepository


class StatisticsRepository(BaseRepository):
    def __init__(self):
        super().__init__(Statistics)

    def get_statistics(self) -> Statistics:
        statistics = self.model.query.first()
        if statistics is None:
            # If no registry exists, create a new registry with default values
            statistics = Statistics(
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
