import pytest

from app.features.statistics.repositories import StatisticsRepository

pytestmark = pytest.mark.repository


def test_get_statistics_creates_and_reuses_the_singleton(test_app, clean_database):
    repo = StatisticsRepository()

    stats = repo.get_statistics()

    assert stats.id is not None
    assert repo.get_statistics().id == stats.id


def test_increment_fields_accumulate(test_app, clean_database):
    repo = StatisticsRepository()

    assert repo.increment_datasets_viewed() == 1
    assert repo.increment_datasets_viewed() == 2
    assert repo.get_datasets_viewed() == 2


def test_increment_feature_models_downloaded(test_app, clean_database):
    repo = StatisticsRepository()

    repo.increment_feature_models_downloaded()

    assert repo.get_feature_models_downloaded() == 1
