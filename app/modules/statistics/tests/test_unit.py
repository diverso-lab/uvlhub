from unittest.mock import patch

import pytest

from app.modules.auth.repositories import UserRepository
from app.modules.dataset.models import PublicationType
from app.modules.dataset.repositories import (
    DataSetRepository,
    DSDownloadRecordRepository,
    DSMetaDataRepository,
    DSViewRecordRepository,
)
from app.modules.featuremodel.repositories import FeatureModelRepository
from app.modules.hubfile.repositories import (
    HubfileDownloadRecordRepository,
    HubfileRepository,
    HubfileViewRecordRepository,
)
from app.modules.statistics.services import StatisticsService


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Add HERE new elements to the database that you want to exist in the test context.
        # DO NOT FORGET to use db.session.add(<element>) and db.session.commit() to save the data.
        pass

    yield test_client


def test_sample_assertion(test_client):
    """
    Sample test to verify that the test framework and environment are working correctly.
    It does not communicate with the Flask application; it only performs a simple assertion to
    confirm that the tests in this module can be executed.
    """
    greeting = "Hello, World!"
    assert greeting == "Hello, World!", "The greeting does not coincide with 'Hello, World!'"


@patch("core.managers.task_queue_manager.TaskQueueManager.enqueue_task")
def test_refresh_statistics_rebuilds_counters_from_records(mock_enqueue_task, test_client, clean_database):
    user = UserRepository().create(email="stats@example.com", password="test1234")

    dsmetadata = DSMetaDataRepository().create(
        title="Stats dataset",
        description="Stats dataset",
        publication_type=PublicationType.BOOK,
        dataset_doi="10.1234/stats-dataset",
    )
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=dsmetadata.id)
    feature_model = FeatureModelRepository().create(dataset_id=dataset.id)
    hubfile = HubfileRepository().create(
        name="stats.uvl",
        checksum="abc123",
        size=123,
        feature_model_id=feature_model.id,
    )

    DSViewRecordRepository().create(dataset_id=dataset.id, view_cookie="view-1")
    DSViewRecordRepository().create(dataset_id=dataset.id, view_cookie="view-2")
    DSDownloadRecordRepository().create(dataset_id=dataset.id, download_cookie="download-1")

    HubfileViewRecordRepository().create(file_id=hubfile.id, view_cookie="file-view-1")
    HubfileViewRecordRepository().create(file_id=hubfile.id, view_cookie="file-view-2")
    HubfileViewRecordRepository().create(file_id=hubfile.id, view_cookie="file-view-3")
    HubfileDownloadRecordRepository().create(file_id=hubfile.id, download_cookie="file-download-1")

    statistics = StatisticsService().refresh_statistics()

    assert statistics.datasets_viewed == 2
    assert statistics.feature_models_viewed == 3
    assert statistics.datasets_downloaded == 1
    assert statistics.feature_models_downloaded == 1
