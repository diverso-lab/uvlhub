import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone

from flask import current_app
from sqlalchemy import func

from app import db
from app.modules.statistics.models import Statistics
from app.modules.statistics.repositories import StatisticsRepository
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard DTO
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class DashboardRow:
    """One row in a top-N table. `detail` is either a count or a date string."""

    title: str
    doi_url: str
    value: int | str


@dataclass
class DashboardData:
    # Summary counters
    total_datasets: int = 0
    total_feature_models: int = 0
    total_authors: int = 0
    total_views: int = 0
    total_downloads: int = 0
    avg_models_per_dataset: float = 0.0

    # Top-N tables
    top_by_models: list[DashboardRow] = field(default_factory=list)
    top_by_features: list[DashboardRow] = field(default_factory=list)
    top_by_views: list[DashboardRow] = field(default_factory=list)
    top_by_downloads: list[DashboardRow] = field(default_factory=list)
    top_by_configurations: list[DashboardRow] = field(default_factory=list)
    latest_datasets: list[DashboardRow] = field(default_factory=list)

    # Other aggregates
    publication_types: list[tuple[str, int]] = field(default_factory=list)

    # Complete 12-month range, same x-axis for every chart.
    months: list[str] = field(default_factory=list)
    uploads_per_month: list[int] = field(default_factory=list)
    views_per_month: list[int] = field(default_factory=list)
    downloads_per_month: list[int] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Existing statistics counters (untouched public API)
# ─────────────────────────────────────────────────────────────────────────────


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

    def refresh_statistics(self) -> Statistics:
        return self.repository.refresh_statistics()


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard service — all the aggregations in one place.
# ─────────────────────────────────────────────────────────────────────────────


class DashboardService:
    """Builds the aggregated view backing `/statistics`.

    The reason this lives in its own class (rather than inside the
    counters-oriented `StatisticsService` above) is that the dashboard is a
    cross-model read model — it joins dataset/feature-model/metric data and
    has nothing to do with the running counters. Keeping them separate also
    makes it cheap to cache the dashboard output while leaving the counters
    write-through.
    """

    CACHE_TTL_SECONDS = 300
    CACHE_KEY = "statistics:dashboard:v1"
    TOP_N = 5
    WINDOW_DAYS = 365
    # `dataset.ds_meta_data.title | truncate(50)` in the template used to vary
    # from 40 to 50 depending on the table; centralise it here.
    TITLE_MAX_LEN = 50

    def build_dashboard(self, use_cache: bool = True) -> DashboardData:
        if use_cache:
            cached = self._cache_get()
            if cached is not None:
                return cached

        data = self._build_dashboard_uncached()

        if use_cache:
            self._cache_set(data)
        return data

    def invalidate_cache(self) -> None:
        """Drop the cached dashboard (call after bulk imports / seeders)."""
        client = self._redis_client()
        if client is not None:
            try:
                client.delete(self.CACHE_KEY)
            except Exception:
                logger.exception("dashboard cache invalidate failed")

    # ── internal ────────────────────────────────────────────────────────────

    def _build_dashboard_uncached(self) -> DashboardData:
        from app.modules.dataset.models import (
            Author,
            DataSet,
            DSDownloadRecord,
            DSMetaData,
            DSMetrics,
            DSViewRecord,
        )
        from app.modules.featuremodel.models import FeatureModel

        # Use UTC consistently with how Flask / DB timestamps are written.
        window_start = datetime.now(timezone.utc) - timedelta(days=self.WINDOW_DAYS)
        window_start_naive = window_start.replace(tzinfo=None)

        # --- Base: only datasets with a DOI are public, every aggregation
        # uses this same filter. One join helper so it can't drift. ---
        def public_datasets_q():
            return (
                db.session.query(DataSet)
                .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
                .filter(DSMetaData.dataset_doi.isnot(None))
            )

        total_datasets = public_datasets_q().count()
        total_feature_models = (
            db.session.query(FeatureModel)
            .join(DataSet, DataSet.id == FeatureModel.dataset_id)
            .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .count()
        )
        total_authors = db.session.query(Author).count()

        counters = StatisticsService()
        total_views = counters.get_datasets_viewed()
        total_downloads = counters.get_datasets_downloaded()

        # --- Tops ---
        top_by_models = self._top_by_feature_model_count(DataSet, DSMetaData, FeatureModel)
        top_by_features = self._top_by_metric(DataSet, DSMetaData, DSMetrics, DSMetrics.number_of_features)
        top_by_views = self._top_by_record_count(DataSet, DSMetaData, DSViewRecord)
        top_by_downloads = self._top_by_record_count(DataSet, DSMetaData, DSDownloadRecord)
        top_by_configurations = self._top_by_metric(DataSet, DSMetaData, DSMetrics, DSMetrics.number_of_models)
        latest_datasets = self._latest_datasets(DataSet, DSMetaData)

        # --- Pub-type breakdown ---
        publication_types_raw = (
            db.session.query(DSMetaData.publication_type, func.count(DataSet.id).label("count"))
            .join(DataSet, DataSet.ds_meta_data_id == DSMetaData.id)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .filter(DSMetaData.publication_type.isnot(None))
            .group_by(DSMetaData.publication_type)
            .order_by(func.count(DataSet.id).desc())
            .all()
        )
        publication_types = [(self._pretty_enum(pt), c) for pt, c in publication_types_raw]

        # --- Monthly rollups (server-side group-by, DOI-filtered) ---
        months = self._month_labels(window_start_naive)

        uploads_raw = (
            db.session.query(
                func.date_format(DataSet.created_at, "%Y-%m").label("ym"),
                func.count(DataSet.id),
            )
            .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .filter(DataSet.created_at >= window_start_naive)
            .group_by("ym")
            .all()
        )

        views_raw = (
            db.session.query(
                func.date_format(DSViewRecord.view_date, "%Y-%m").label("ym"),
                func.count(DSViewRecord.id),
            )
            .join(DataSet, DataSet.id == DSViewRecord.dataset_id)
            .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .filter(DSViewRecord.view_date >= window_start_naive)
            .group_by("ym")
            .all()
        )

        downloads_raw = (
            db.session.query(
                func.date_format(DSDownloadRecord.download_date, "%Y-%m").label("ym"),
                func.count(DSDownloadRecord.id),
            )
            .join(DataSet, DataSet.id == DSDownloadRecord.dataset_id)
            .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .filter(DSDownloadRecord.download_date >= window_start_naive)
            .group_by("ym")
            .all()
        )

        uploads_per_month = self._align_to_months(months, uploads_raw)
        views_per_month = self._align_to_months(months, views_raw)
        downloads_per_month = self._align_to_months(months, downloads_raw)

        avg = round(total_feature_models / total_datasets, 2) if total_datasets else 0.0

        return DashboardData(
            total_datasets=total_datasets,
            total_feature_models=total_feature_models,
            total_authors=total_authors,
            total_views=total_views,
            total_downloads=total_downloads,
            avg_models_per_dataset=avg,
            top_by_models=top_by_models,
            top_by_features=top_by_features,
            top_by_views=top_by_views,
            top_by_downloads=top_by_downloads,
            top_by_configurations=top_by_configurations,
            latest_datasets=latest_datasets,
            publication_types=publication_types,
            months=months,
            uploads_per_month=uploads_per_month,
            views_per_month=views_per_month,
            downloads_per_month=downloads_per_month,
        )

    # ── top-N helpers ──────────────────────────────────────────────────────

    def _top_by_feature_model_count(self, DataSet, DSMetaData, FeatureModel) -> list[DashboardRow]:
        rows = (
            db.session.query(DataSet, func.count(FeatureModel.id).label("fm_count"))
            .join(FeatureModel, DataSet.id == FeatureModel.dataset_id)
            .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .group_by(DataSet.id)
            .order_by(func.count(FeatureModel.id).desc())
            .limit(self.TOP_N)
            .all()
        )
        return [self._row(ds, count) for ds, count in rows]

    def _top_by_metric(self, DataSet, DSMetaData, DSMetrics, column) -> list[DashboardRow]:
        rows = (
            db.session.query(DataSet, column)
            .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
            .join(DSMetrics, DSMetaData.ds_metrics_id == DSMetrics.id)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .filter(column.isnot(None))
            .order_by(column.desc())
            .limit(self.TOP_N)
            .all()
        )
        return [self._row(ds, value) for ds, value in rows]

    def _top_by_record_count(self, DataSet, DSMetaData, RecordModel) -> list[DashboardRow]:
        rows = (
            db.session.query(DataSet, func.count(RecordModel.id).label("count"))
            .join(RecordModel, DataSet.id == RecordModel.dataset_id)
            .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .group_by(DataSet.id)
            .order_by(func.count(RecordModel.id).desc())
            .limit(self.TOP_N)
            .all()
        )
        return [self._row(ds, count) for ds, count in rows]

    def _latest_datasets(self, DataSet, DSMetaData) -> list[DashboardRow]:
        rows = (
            db.session.query(DataSet)
            .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .order_by(DataSet.created_at.desc())
            .limit(self.TOP_N)
            .all()
        )
        return [self._row(ds, ds.created_at.strftime("%d %b %Y")) for ds in rows]

    # ── small utilities ────────────────────────────────────────────────────

    def _row(self, dataset, value) -> DashboardRow:
        title = (dataset.ds_meta_data.title or "")[: self.TITLE_MAX_LEN]
        if len(dataset.ds_meta_data.title or "") > self.TITLE_MAX_LEN:
            title += "…"
        try:
            doi_url = dataset.get_uvlhub_doi()
        except Exception:
            doi_url = "#"
        return DashboardRow(title=title, doi_url=doi_url, value=value)

    @staticmethod
    def _pretty_enum(value) -> str:
        if value is None:
            return "—"
        name = getattr(value, "name", str(value))
        return name.replace("_", " ").title()

    @staticmethod
    def _month_labels(start_naive: datetime) -> list[str]:
        """Every YYYY-MM from `start` up to today, inclusive, no gaps."""
        labels: list[str] = []
        cur = datetime(start_naive.year, start_naive.month, 1)
        today = datetime.utcnow()
        end = datetime(today.year, today.month, 1)
        while cur <= end:
            labels.append(cur.strftime("%Y-%m"))
            # step forward 1 month
            if cur.month == 12:
                cur = datetime(cur.year + 1, 1, 1)
            else:
                cur = datetime(cur.year, cur.month + 1, 1)
        return labels

    @staticmethod
    def _align_to_months(months: list[str], rows) -> list[int]:
        table = {ym: count for ym, count in rows if ym is not None}
        return [int(table.get(m, 0)) for m in months]

    # ── cache ──────────────────────────────────────────────────────────────

    def _redis_client(self):
        """Return a Redis client or None if caching is unavailable/disabled.

        Tests use SQLite with an in-process app and frequently rebuild data;
        skip caching there to keep tests deterministic.
        """
        if current_app.config.get("TESTING"):
            return None
        try:
            return current_app.config.get("SESSION_REDIS")
        except Exception:
            return None

    def _cache_get(self) -> DashboardData | None:
        client = self._redis_client()
        if client is None:
            return None
        try:
            raw = client.get(self.CACHE_KEY)
        except Exception:
            logger.exception("dashboard cache read failed")
            return None
        if not raw:
            return None
        try:
            payload = json.loads(raw)
        except Exception:
            logger.exception("dashboard cache decode failed")
            return None
        return self._from_cached_payload(payload)

    def _cache_set(self, data: DashboardData) -> None:
        client = self._redis_client()
        if client is None:
            return
        try:
            client.setex(self.CACHE_KEY, self.CACHE_TTL_SECONDS, json.dumps(self._to_cached_payload(data)))
        except Exception:
            logger.exception("dashboard cache write failed")

    @staticmethod
    def _to_cached_payload(data: DashboardData) -> dict:
        payload = asdict(data)
        # Convert tuples to lists so JSON round-trip is lossless.
        payload["publication_types"] = [list(pt) for pt in data.publication_types]
        return payload

    @staticmethod
    def _from_cached_payload(payload: dict) -> DashboardData:
        def rows(key):
            return [DashboardRow(**r) for r in payload.get(key, [])]

        return DashboardData(
            total_datasets=payload.get("total_datasets", 0),
            total_feature_models=payload.get("total_feature_models", 0),
            total_authors=payload.get("total_authors", 0),
            total_views=payload.get("total_views", 0),
            total_downloads=payload.get("total_downloads", 0),
            avg_models_per_dataset=payload.get("avg_models_per_dataset", 0.0),
            top_by_models=rows("top_by_models"),
            top_by_features=rows("top_by_features"),
            top_by_views=rows("top_by_views"),
            top_by_downloads=rows("top_by_downloads"),
            top_by_configurations=rows("top_by_configurations"),
            latest_datasets=rows("latest_datasets"),
            publication_types=[tuple(pt) for pt in payload.get("publication_types", [])],
            months=payload.get("months", []),
            uploads_per_month=payload.get("uploads_per_month", []),
            views_per_month=payload.get("views_per_month", []),
            downloads_per_month=payload.get("downloads_per_month", []),
        )
