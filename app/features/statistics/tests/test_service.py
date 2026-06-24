from unittest.mock import patch

import pytest

from app.features.auth.repositories import UserRepository
from app.features.dataset.models import PublicationType
from app.features.dataset.repositories import (
    DataSetRepository,
    DSDownloadRecordRepository,
    DSMetaDataRepository,
    DSViewRecordRepository,
)
from app.features.featuremodel.repositories import FeatureModelRepository
from app.features.hubfile.repositories import (
    HubfileDownloadRecordRepository,
    HubfileRepository,
    HubfileViewRecordRepository,
)
from app.features.statistics.services import DashboardService, StatisticsService

pytestmark = pytest.mark.service


@patch("app.managers.task_queue_manager.TaskQueueManager.enqueue_task")
def test_refresh_statistics_rebuilds_counters_from_records(_enqueue, test_app, clean_database):
    user = UserRepository().create(email="stats@example.com", password="test1234")
    meta = DSMetaDataRepository().create(
        title="Stats dataset", description="Stats", publication_type=PublicationType.BOOK, dataset_doi="10.1/stats"
    )
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)
    feature_model = FeatureModelRepository().create(dataset_id=dataset.id)
    hubfile = HubfileRepository().create(
        name="stats.uvl", checksum="abc", size=123, feature_model_id=feature_model.id, dataset_id=dataset.id
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


@patch("app.managers.task_queue_manager.TaskQueueManager.enqueue_task")
def test_refresh_statistics_excludes_private_datasets(_enqueue, test_app, clean_database):
    user = UserRepository().create(email="stats-private@example.com", password="test1234")

    public_meta = DSMetaDataRepository().create(
        title="Public", description="Public", publication_type=PublicationType.BOOK, dataset_doi="10.1/public"
    )
    public_ds = DataSetRepository().create(user_id=user.id, ds_meta_data_id=public_meta.id)
    public_fm = FeatureModelRepository().create(dataset_id=public_ds.id)
    public_hubfile = HubfileRepository().create(
        name="public.uvl", checksum="p", size=1, feature_model_id=public_fm.id, dataset_id=public_ds.id
    )
    DSViewRecordRepository().create(dataset_id=public_ds.id, view_cookie="pub-v")
    DSDownloadRecordRepository().create(dataset_id=public_ds.id, download_cookie="pub-d")
    HubfileViewRecordRepository().create(file_id=public_hubfile.id, view_cookie="pub-fv")
    HubfileDownloadRecordRepository().create(file_id=public_hubfile.id, download_cookie="pub-fd")

    private_meta = DSMetaDataRepository().create(
        title="Private", description="Private", publication_type=PublicationType.BOOK, dataset_doi=None
    )
    private_ds = DataSetRepository().create(user_id=user.id, ds_meta_data_id=private_meta.id)
    private_fm = FeatureModelRepository().create(dataset_id=private_ds.id)
    private_hubfile = HubfileRepository().create(
        name="priv.uvl", checksum="pr", size=1, feature_model_id=private_fm.id, dataset_id=private_ds.id
    )
    DSViewRecordRepository().create(dataset_id=private_ds.id, view_cookie="priv-v")
    DSDownloadRecordRepository().create(dataset_id=private_ds.id, download_cookie="priv-d")
    HubfileViewRecordRepository().create(file_id=private_hubfile.id, view_cookie="priv-fv")
    HubfileDownloadRecordRepository().create(file_id=private_hubfile.id, download_cookie="priv-fd")

    stats = StatisticsService().refresh_statistics()

    assert stats.datasets_counter == 1
    assert stats.feature_models_counter == 1
    assert stats.datasets_viewed == 1
    assert stats.datasets_downloaded == 1
    assert stats.feature_models_viewed == 1
    assert stats.feature_models_downloaded == 1


def test_preview_refresh_returns_before_after_tuples(test_app, clean_database):
    user = UserRepository().create(email="preview@example.com", password="test1234")
    meta = DSMetaDataRepository().create(
        title="Preview", description="Preview", publication_type=PublicationType.BOOK, dataset_doi="10.9/preview"
    )
    ds = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)
    FeatureModelRepository().create(dataset_id=ds.id)

    service = StatisticsService()
    diff = service.preview_refresh()

    persisted = service.get_statistics()
    assert persisted.datasets_counter == 0
    assert persisted.feature_models_counter == 0
    assert diff["datasets_counter"] == (0, 1)
    assert diff["feature_models_counter"] == (0, 1)


def _seed_dashboard_fixtures():
    user = UserRepository().create(email="dash@example.com", password="test1234")

    popular_meta = DSMetaDataRepository().create(
        title="Popular dataset",
        description="Popular",
        publication_type=PublicationType.JOURNAL_ARTICLE,
        dataset_doi="10.9/popular",
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
        dataset_doi="10.9/quiet",
    )
    quiet = DataSetRepository().create(user_id=user.id, ds_meta_data_id=quiet_meta.id)
    FeatureModelRepository().create(dataset_id=quiet.id)

    private_meta = DSMetaDataRepository().create(
        title="Private dataset",
        description="No DOI",
        publication_type=PublicationType.JOURNAL_ARTICLE,
        dataset_doi=None,
    )
    private = DataSetRepository().create(user_id=user.id, ds_meta_data_id=private_meta.id)
    FeatureModelRepository().create(dataset_id=private.id)
    DSViewRecordRepository().create(dataset_id=private.id, view_cookie="v-priv")


def test_dashboard_excludes_datasets_without_doi(test_app, clean_database):
    _seed_dashboard_fixtures()

    data = DashboardService().build_dashboard(use_cache=False)

    assert data.total_datasets == 2
    assert data.total_feature_models == 3
    titles = [row.title for row in data.top_by_models]
    assert "Private dataset" not in titles
    assert "Popular dataset" in titles


def test_dashboard_monthly_series_has_no_gaps(test_app, clean_database):
    _seed_dashboard_fixtures()

    data = DashboardService().build_dashboard(use_cache=False)

    assert len(data.months) >= 12
    assert len(data.uploads_per_month) == len(data.months)
    assert data.months == sorted(data.months)


def test_dashboard_top_tables_are_ordered_by_metric(test_app, clean_database):
    _seed_dashboard_fixtures()

    data = DashboardService().build_dashboard(use_cache=False)

    assert [row.title for row in data.top_by_models][0] == "Popular dataset"
    assert [row.title for row in data.top_by_views][0] == "Popular dataset"


def test_dashboard_is_deterministic_between_calls(test_app, clean_database):
    _seed_dashboard_fixtures()
    service = DashboardService()

    assert service.build_dashboard(use_cache=True) == service.build_dashboard(use_cache=True)


def test_dashboard_corpus_aggregates_hubfile_metrics(test_app, clean_database):
    from app import db
    from app.features.factlabel.models import HubfileMetrics

    user = UserRepository().create(email="corpus@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(
        title="Corpus", description="d", publication_type=PublicationType.BOOK, dataset_doi="10.1/corpus"
    )
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)
    fm = FeatureModelRepository().create(dataset_id=dataset.id)
    for i, features in enumerate((10, 20, 30)):
        hubfile = HubfileRepository().create(
            name=f"m{i}.uvl", checksum=str(i), size=1, feature_model_id=fm.id, dataset_id=dataset.id
        )
        db.session.add(
            HubfileMetrics(
                hubfile_id=hubfile.id,
                extractor_version="1",
                parse_error=None,
                features=features,
                cross_tree_constraints=i,
                depth_of_tree=2,
                satisfiable=True,
            )
        )
    db.session.commit()

    corpus = DashboardService().build_dashboard(use_cache=False).corpus

    assert corpus.metrics_rows == 3
    assert corpus.metrics_ok == 3
    assert corpus.summary_features.count == 3
    assert corpus.summary_features.max == 30.0
    assert corpus.satisfiable_count == 3
    assert len(corpus.top_by_features) == 3
