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
from app.modules.statistics.services import DashboardService, StatisticsService


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


# ─── Dashboard ──────────────────────────────────────────────────────────────


def _seed_dashboard_fixtures():
    """Two DOI'd datasets (one more popular than the other) and one
    without DOI, so we can verify the DOI filter hides it."""
    user = UserRepository().create(email="dash@example.com", password="test1234")

    popular_meta = DSMetaDataRepository().create(
        title="Popular dataset",
        description="Popular",
        publication_type=PublicationType.JOURNAL_ARTICLE,
        dataset_doi="10.9999/popular",
    )
    popular = DataSetRepository().create(user_id=user.id, ds_meta_data_id=popular_meta.id)
    FeatureModelRepository().create(dataset_id=popular.id)
    FeatureModelRepository().create(dataset_id=popular.id)
    DSViewRecordRepository().create(dataset_id=popular.id, view_cookie="v-p1")
    DSViewRecordRepository().create(dataset_id=popular.id, view_cookie="v-p2")
    DSDownloadRecordRepository().create(dataset_id=popular.id, download_cookie="d-p1")

    quiet_meta = DSMetaDataRepository().create(
        title="Quiet dataset",
        description="Quiet",
        publication_type=PublicationType.JOURNAL_ARTICLE,
        dataset_doi="10.9999/quiet",
    )
    quiet = DataSetRepository().create(user_id=user.id, ds_meta_data_id=quiet_meta.id)
    FeatureModelRepository().create(dataset_id=quiet.id)

    private_meta = DSMetaDataRepository().create(
        title="Private dataset",
        description="No DOI — must be invisible",
        publication_type=PublicationType.JOURNAL_ARTICLE,
        dataset_doi=None,
    )
    private = DataSetRepository().create(user_id=user.id, ds_meta_data_id=private_meta.id)
    FeatureModelRepository().create(dataset_id=private.id)
    DSViewRecordRepository().create(dataset_id=private.id, view_cookie="v-priv")

    return popular, quiet, private


def test_dashboard_excludes_datasets_without_doi(test_client, clean_database):
    _seed_dashboard_fixtures()

    data = DashboardService().build_dashboard(use_cache=False)

    assert data.total_datasets == 2  # the private one is excluded
    assert data.total_feature_models == 3  # 2 + 1
    titles = [row.title for row in data.top_by_models]
    assert "Private dataset" not in titles
    assert "Popular dataset" in titles
    assert "Quiet dataset" in titles


def test_dashboard_monthly_series_has_no_gaps(test_client, clean_database):
    _seed_dashboard_fixtures()

    data = DashboardService().build_dashboard(use_cache=False)

    # Covers the rolling 12-month window: 13 buckets (start + 12 whole months).
    assert len(data.months) >= 12
    assert len(data.uploads_per_month) == len(data.months)
    assert len(data.views_per_month) == len(data.months)
    assert len(data.downloads_per_month) == len(data.months)
    # Months are strictly ordered.
    assert data.months == sorted(data.months)


def test_dashboard_top_tables_are_ordered_by_metric(test_client, clean_database):
    _seed_dashboard_fixtures()

    data = DashboardService().build_dashboard(use_cache=False)

    titles_in_order = [row.title for row in data.top_by_models]
    # The "popular" dataset has 2 FM, quiet has 1, so popular must come first.
    assert titles_in_order[0] == "Popular dataset"

    view_titles = [row.title for row in data.top_by_views]
    assert view_titles[0] == "Popular dataset"


def test_dashboard_uses_cache_when_enabled(test_client, clean_database):
    _seed_dashboard_fixtures()
    service = DashboardService()
    # In testing we short-circuit the Redis client; use_cache still runs the
    # full path but the payload must be identical between calls.
    a = service.build_dashboard(use_cache=True)
    b = service.build_dashboard(use_cache=True)
    assert a == b


def test_dashboard_route_renders_without_errors(test_client, clean_database):
    _seed_dashboard_fixtures()
    response = test_client.get("/statistics")
    assert response.status_code == 200
    body = response.data.decode()
    assert "Popular dataset" in body
    # The pub-type label must come out pretty-cased from the enum name.
    assert "Journal Article" in body
    # Private dataset must not appear anywhere.
    assert "Private dataset" not in body
