from app.modules.statistics.models import Statistics
from core.seeders.BaseSeeder import BaseSeeder


class StatisticsSeeder(BaseSeeder):

    def run(self):

        data = [
            Statistics(
                datasets_viewed=0,
                feature_models_viewed=0,
                datasets_downloaded=0,
                feature_models_downloaded=0,
            )
        ]

        self.seed(data)
