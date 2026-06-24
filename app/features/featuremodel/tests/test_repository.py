import pytest

from app.features.featuremodel.repositories import FeatureModelRepository

pytestmark = pytest.mark.repository


def test_count_feature_models_is_zero_on_an_empty_database(test_app, clean_database):
    assert FeatureModelRepository().count_feature_models() == 0
