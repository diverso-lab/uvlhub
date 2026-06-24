import pytest

from app.features.auth.repositories import UserRepository
from app.features.dataset.models import PublicationType
from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository, DSViewRecordRepository
from app.features.featuremodel.repositories import FeatureModelRepository

pytestmark = pytest.mark.integration


def test_dashboard_route_renders_without_errors(test_client, clean_database):
    user = UserRepository().create(email="dashint@example.com", password="test1234")
    meta = DSMetaDataRepository().create(
        title="Popular dataset",
        description="Popular",
        publication_type=PublicationType.JOURNAL_ARTICLE,
        dataset_doi="10.9/popular",
    )
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)
    FeatureModelRepository().create(dataset_id=dataset.id)
    DSViewRecordRepository().create(dataset_id=dataset.id, view_cookie="v1")

    response = test_client.get("/statistics")

    assert response.status_code == 200
    body = response.data.decode()
    assert "Popular dataset" in body
    assert "Journal Article" in body


def test_export_csv_streams_a_csv(test_client):
    response = test_client.get("/statistics/export.csv")

    assert response.status_code == 200
    assert response.mimetype == "text/csv"


def test_export_json_streams_json(test_client):
    response = test_client.get("/statistics/export.json")

    assert response.status_code == 200
    assert response.mimetype == "application/json"
