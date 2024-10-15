from app.modules.statistics.models import Statistics
from app.modules.statistics.repositories import StatisticsRepository
from core.services.BaseService import BaseService


class StatisticsService(BaseService):
    def __init__(self):
        super().__init__(StatisticsRepository())

    def get_statistics(self) -> Statistics:
        return self.repository.get_statistics()

    # Incremental methods
    def increment_datasets_viewed(self) -> int:
        return self.repository.increment_datasets_viewed()

    def increment_feature_models_viewed(self) -> int:
        return self.repository.increment_feature_models_viewed()

    def increment_datasets_downloaded(self) -> int:
        return self.repository.increment_datasets_downloaded()

    def increment_feature_models_downloaded(self) -> int:
        return self.repository.increment_feature_models_downloaded()

    # Consultation methods
    def get_datasets_viewed(self) -> int:
        return self.repository.get_datasets_viewed()

    def get_feature_models_viewed(self) -> int:
        return self.repository.get_feature_models_viewed()

    def get_datasets_downloaded(self) -> int:
        return self.repository.get_datasets_downloaded()

    def get_feature_models_downloaded(self) -> int:
        return self.repository.get_feature_models_downloaded()
