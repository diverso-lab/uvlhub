import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from statistics import median, quantiles, stdev

from flask import current_app
from sqlalchemy import case, func

from app import db
from app.modules.statistics.models import Statistics
from app.modules.statistics.repositories import StatisticsRepository
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard DTOs
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class DashboardRow:
    """One row in a top-N table. `value` is either a count or a date string."""

    title: str
    doi_url: str
    value: int | str


@dataclass
class StatsSummary:
    """Five-number summary + mean/std for one numeric series.

    Mirrors what most FM-corpus papers print: min/Q1/median/Q3/max plus a
    mean and stddev for the parametric crowd. Computed in Python from a
    single pulled column — O(N) over <2k rows is negligible and beats
    DB-version-specific PERCENTILE_CONT plumbing.
    """

    count: int = 0
    min: float | None = None
    q1: float | None = None
    median: float | None = None
    q3: float | None = None
    p90: float | None = None
    max: float | None = None
    mean: float | None = None
    stddev: float | None = None


@dataclass
class HistogramBucket:
    label: str
    count: int


@dataclass
class CorpusData:
    """Corpus-characterisation block of the dashboard.

    All numbers are aggregations over the materialised `hubfile_metrics`
    table — no JSON parsing happens at request time.
    """

    # Coverage
    total_hubfiles: int = 0
    hubfiles_with_factlabel: int = 0
    metrics_rows: int = 0
    metrics_ok: int = 0
    metrics_errored: int = 0
    coverage_pct: float = 0.0

    # Semantic outcomes
    satisfiable_count: int = 0
    unsatisfiable_count: int = 0
    unknown_satisfiability: int = 0
    satisfiable_pct: float = 0.0

    # Five-number summaries (the headline numerical tables for the paper).
    summary_features: StatsSummary = field(default_factory=StatsSummary)
    summary_constraints: StatsSummary = field(default_factory=StatsSummary)
    summary_depth: StatsSummary = field(default_factory=StatsSummary)
    summary_branching_factor: StatsSummary = field(default_factory=StatsSummary)
    summary_configurations: StatsSummary = field(default_factory=StatsSummary)

    # Distributions (log-bucketed for size; linear for depth).
    features_histogram: list[HistogramBucket] = field(default_factory=list)
    constraints_histogram: list[HistogramBucket] = field(default_factory=list)
    depth_histogram: list[HistogramBucket] = field(default_factory=list)
    configurations_histogram: list[HistogramBucket] = field(default_factory=list)

    # Composition breakdowns (sum across the whole corpus).
    constraint_types: list[tuple[str, int]] = field(default_factory=list)
    group_types: list[tuple[str, int]] = field(default_factory=list)
    feature_classification: list[tuple[str, int]] = field(default_factory=list)

    # Tops by complexity (per hubfile).
    top_by_features: list[DashboardRow] = field(default_factory=list)
    top_by_constraints: list[DashboardRow] = field(default_factory=list)
    top_by_configurations: list[DashboardRow] = field(default_factory=list)


@dataclass
class DashboardData:
    # --- Platform usage (existing API) ---
    total_datasets: int = 0
    total_feature_models: int = 0
    total_authors: int = 0
    total_views: int = 0
    total_downloads: int = 0
    avg_models_per_dataset: float = 0.0

    top_by_models: list[DashboardRow] = field(default_factory=list)
    top_by_features: list[DashboardRow] = field(default_factory=list)
    top_by_views: list[DashboardRow] = field(default_factory=list)
    top_by_downloads: list[DashboardRow] = field(default_factory=list)
    top_by_configurations: list[DashboardRow] = field(default_factory=list)
    latest_datasets: list[DashboardRow] = field(default_factory=list)

    publication_types: list[tuple[str, int]] = field(default_factory=list)

    months: list[str] = field(default_factory=list)
    uploads_per_month: list[int] = field(default_factory=list)
    views_per_month: list[int] = field(default_factory=list)
    downloads_per_month: list[int] = field(default_factory=list)

    # --- Corpus characterisation (new, backed by hubfile_metrics) ---
    corpus: CorpusData = field(default_factory=CorpusData)


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

    def preview_refresh(self) -> dict[str, tuple[int, int]]:
        """Dry-run sync: return ``{field: (before, after)}`` without writing.

        Used by `rosemary counters:sync --dry-run` so operators can inspect
        drift before committing. Every dict key is also a real field on
        :class:`Statistics`, so callers can feed it straight into a template.
        """
        current = self.repository.get_statistics()
        proposed = self.repository.compute_totals()
        return {field: (getattr(current, field), value) for field, value in proposed.items()}


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard service — all the aggregations in one place.
# ─────────────────────────────────────────────────────────────────────────────


# Log-spaced buckets for size-like quantities (features, constraints) — the
# distribution of FM sizes is heavy-tailed in every corpus paper I've seen,
# so a linear histogram would put 95% of the mass into one bar.
_SIZE_BUCKETS: list[tuple[str, int, int | None]] = [
    ("0–9", 0, 10),
    ("10–49", 10, 50),
    ("50–99", 50, 100),
    ("100–499", 100, 500),
    ("500–999", 500, 1000),
    ("1k–4.9k", 1000, 5000),
    ("5k–9.9k", 5000, 10000),
    ("≥10k", 10000, None),
]


_CONFIG_BUCKETS: list[tuple[str, int, int | None]] = [
    ("1", 1, 2),
    ("2–9", 2, 10),
    ("10–99", 10, 100),
    ("100–999", 100, 1000),
    ("1k–9.9k", 1000, 10000),
    ("10k–99k", 10000, 100000),
    ("100k–999k", 100000, 1_000_000),
    ("≥1M", 1_000_000, None),
]


class DashboardService:
    """Builds the aggregated view backing `/statistics`.

    Two logical sections:
      * Platform usage  — datasets/views/downloads activity (existing).
      * Corpus          — structural and semantic characterisation of the
                          feature models, sourced from `hubfile_metrics`.
    """

    # Cache key bumped to v2 because the schema gained the corpus block.
    CACHE_TTL_SECONDS = 300
    CACHE_KEY = "statistics:dashboard:v2"
    TOP_N = 5
    TOP_N_CORPUS = 10
    WINDOW_DAYS = 365
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

        # Only datasets with a DOI are considered "public", every aggregation
        # uses this same filter.
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

        # --- Platform tops ---
        top_by_models = self._top_by_feature_model_count(DataSet, DSMetaData, FeatureModel)
        top_by_features = self._top_by_metric(DataSet, DSMetaData, DSMetrics, DSMetrics.number_of_features)
        top_by_views = self._top_by_record_count(DataSet, DSMetaData, DSViewRecord)
        top_by_downloads = self._top_by_record_count(DataSet, DSMetaData, DSDownloadRecord)
        top_by_configurations = self._top_by_metric(DataSet, DSMetaData, DSMetrics, DSMetrics.number_of_models)
        latest_datasets = self._latest_datasets(DataSet, DSMetaData)

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

        # --- Monthly rollups ---
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

        # --- Corpus block ---
        corpus = self._build_corpus()

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
            corpus=corpus,
        )

    # ── corpus block ────────────────────────────────────────────────────────

    def _build_corpus(self) -> CorpusData:
        """Build the corpus characterisation entirely from `hubfile_metrics`.

        Strategy: one big SELECT pulling every row (all columns we need),
        then per-column aggregations in Python. With <10k hubfiles that's
        much simpler than 10 separate aggregate queries and lets us share
        the same row scan for summaries, histograms and breakdowns.
        """
        from app.modules.hubfile.models import Hubfile, HubfileMetrics

        total_hubfiles = db.session.query(func.count(Hubfile.id)).scalar() or 0
        hubfiles_with_factlabel = (
            db.session.query(func.count(Hubfile.id))
            .filter(Hubfile.factlabel_json.isnot(None))
            .filter(Hubfile.factlabel_json != "")
            .scalar()
            or 0
        )

        metrics_total, metrics_ok, metrics_errored = db.session.query(
            func.count(HubfileMetrics.hubfile_id),
            func.sum(case((HubfileMetrics.parse_error.is_(None), 1), else_=0)),
            func.sum(case((HubfileMetrics.parse_error.isnot(None), 1), else_=0)),
        ).one()
        metrics_total = metrics_total or 0
        metrics_ok = int(metrics_ok or 0)
        metrics_errored = int(metrics_errored or 0)

        # Pull every numeric column we summarise/breakdown in one shot.
        rows = (
            db.session.query(
                HubfileMetrics.features,
                HubfileMetrics.cross_tree_constraints,
                HubfileMetrics.depth_of_tree,
                HubfileMetrics.branching_factor,
                HubfileMetrics.configurations,
                HubfileMetrics.configurations_is_upper_bound,
                HubfileMetrics.satisfiable,
                HubfileMetrics.requires_constraints,
                HubfileMetrics.excludes_constraints,
                HubfileMetrics.complex_constraints,
                HubfileMetrics.arithmetic_constraints,
                HubfileMetrics.aggregation_constraints,
                HubfileMetrics.alternative_groups,
                HubfileMetrics.or_groups,
                HubfileMetrics.mutex_groups,
                HubfileMetrics.cardinality_groups,
                HubfileMetrics.core_features,
                HubfileMetrics.dead_features,
                HubfileMetrics.false_optional_features,
                HubfileMetrics.variant_features,
                HubfileMetrics.pure_optional_features,
            )
            .filter(HubfileMetrics.parse_error.is_(None))
            .all()
        )

        features = [r.features for r in rows if r.features is not None]
        constraints = [r.cross_tree_constraints for r in rows if r.cross_tree_constraints is not None]
        depth = [r.depth_of_tree for r in rows if r.depth_of_tree is not None]
        branching = [r.branching_factor for r in rows if r.branching_factor is not None]
        # For the configurations summary we discard upper-bound rows: averaging
        # an exact count with an upper estimate would be misleading.
        configs_exact = [
            r.configurations for r in rows if r.configurations is not None and not r.configurations_is_upper_bound
        ]

        sat_yes = sum(1 for r in rows if r.satisfiable is True)
        sat_no = sum(1 for r in rows if r.satisfiable is False)
        sat_unknown = sum(1 for r in rows if r.satisfiable is None)

        constraint_types = [
            ("Requires", _sum(rows, "requires_constraints")),
            ("Excludes", _sum(rows, "excludes_constraints")),
            ("Complex (logical)", _sum(rows, "complex_constraints")),
            ("Arithmetic", _sum(rows, "arithmetic_constraints")),
            ("Aggregation", _sum(rows, "aggregation_constraints")),
        ]
        group_types = [
            ("Alternative", _sum(rows, "alternative_groups")),
            ("Or", _sum(rows, "or_groups")),
            ("Mutex", _sum(rows, "mutex_groups")),
            ("Cardinality", _sum(rows, "cardinality_groups")),
        ]
        feature_classification = [
            ("Core", _sum(rows, "core_features")),
            ("Dead", _sum(rows, "dead_features")),
            ("False-optional", _sum(rows, "false_optional_features")),
            ("Variant", _sum(rows, "variant_features")),
            ("Pure-optional", _sum(rows, "pure_optional_features")),
        ]

        coverage = (metrics_ok / hubfiles_with_factlabel * 100) if hubfiles_with_factlabel else 0.0
        sat_total = sat_yes + sat_no
        sat_pct = (sat_yes / sat_total * 100) if sat_total else 0.0

        return CorpusData(
            total_hubfiles=int(total_hubfiles),
            hubfiles_with_factlabel=int(hubfiles_with_factlabel),
            metrics_rows=int(metrics_total),
            metrics_ok=metrics_ok,
            metrics_errored=metrics_errored,
            coverage_pct=round(coverage, 2),
            satisfiable_count=sat_yes,
            unsatisfiable_count=sat_no,
            unknown_satisfiability=sat_unknown,
            satisfiable_pct=round(sat_pct, 2),
            summary_features=_summarize(features),
            summary_constraints=_summarize(constraints),
            summary_depth=_summarize(depth),
            summary_branching_factor=_summarize(branching),
            summary_configurations=_summarize(configs_exact),
            features_histogram=_bucket(features, _SIZE_BUCKETS),
            constraints_histogram=_bucket(constraints, _SIZE_BUCKETS),
            depth_histogram=_linear_bucket(depth, max_bucket=15),
            configurations_histogram=_bucket(configs_exact, _CONFIG_BUCKETS),
            constraint_types=constraint_types,
            group_types=group_types,
            feature_classification=feature_classification,
            top_by_features=self._top_corpus_by(HubfileMetrics.features),
            top_by_constraints=self._top_corpus_by(HubfileMetrics.cross_tree_constraints),
            top_by_configurations=self._top_corpus_by(
                HubfileMetrics.configurations,
                extra_filter=HubfileMetrics.configurations_is_upper_bound.is_(False),
            ),
        )

    def _top_corpus_by(self, column, extra_filter=None) -> list[DashboardRow]:
        """Top-N hubfiles ordered by `column` desc, joined back to dataset metadata.

        Uses `Hubfile → FeatureModel → DataSet → DSMetaData` to surface a
        clickable title; the `value` is the raw column value (e.g. number of
        features) for context.
        """
        from app.modules.dataset.models import DataSet, DSMetaData
        from app.modules.featuremodel.models import FeatureModel
        from app.modules.hubfile.models import Hubfile, HubfileMetrics

        q = (
            db.session.query(Hubfile, DataSet, column)
            .join(HubfileMetrics, HubfileMetrics.hubfile_id == Hubfile.id)
            .join(FeatureModel, FeatureModel.id == Hubfile.feature_model_id)
            .join(DataSet, DataSet.id == FeatureModel.dataset_id)
            .join(DSMetaData, DSMetaData.id == DataSet.ds_meta_data_id)
            .filter(HubfileMetrics.parse_error.is_(None))
            .filter(column.isnot(None))
        )
        if extra_filter is not None:
            q = q.filter(extra_filter)
        rows = q.order_by(column.desc()).limit(self.TOP_N_CORPUS).all()

        out: list[DashboardRow] = []
        for hubfile, dataset, value in rows:
            title = f"{(dataset.ds_meta_data.title or '')[: self.TITLE_MAX_LEN]} · {hubfile.name}"
            try:
                doi_url = dataset.get_uvlhub_doi()
            except Exception:
                doi_url = "#"
            out.append(DashboardRow(title=title, doi_url=doi_url, value=int(value) if value is not None else 0))
        return out

    # ── platform top-N helpers ─────────────────────────────────────────────

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
        labels: list[str] = []
        cur = datetime(start_naive.year, start_naive.month, 1)
        today = datetime.utcnow()
        end = datetime(today.year, today.month, 1)
        while cur <= end:
            labels.append(cur.strftime("%Y-%m"))
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
        # Tuples → lists for lossless JSON round-trip.
        payload["publication_types"] = [list(pt) for pt in data.publication_types]
        payload["corpus"]["constraint_types"] = [list(t) for t in data.corpus.constraint_types]
        payload["corpus"]["group_types"] = [list(t) for t in data.corpus.group_types]
        payload["corpus"]["feature_classification"] = [list(t) for t in data.corpus.feature_classification]
        return payload

    @staticmethod
    def _from_cached_payload(payload: dict) -> DashboardData:
        def rows(key, source=payload):
            return [DashboardRow(**r) for r in source.get(key, [])]

        corpus_payload = payload.get("corpus", {})
        corpus = CorpusData(
            total_hubfiles=corpus_payload.get("total_hubfiles", 0),
            hubfiles_with_factlabel=corpus_payload.get("hubfiles_with_factlabel", 0),
            metrics_rows=corpus_payload.get("metrics_rows", 0),
            metrics_ok=corpus_payload.get("metrics_ok", 0),
            metrics_errored=corpus_payload.get("metrics_errored", 0),
            coverage_pct=corpus_payload.get("coverage_pct", 0.0),
            satisfiable_count=corpus_payload.get("satisfiable_count", 0),
            unsatisfiable_count=corpus_payload.get("unsatisfiable_count", 0),
            unknown_satisfiability=corpus_payload.get("unknown_satisfiability", 0),
            satisfiable_pct=corpus_payload.get("satisfiable_pct", 0.0),
            summary_features=StatsSummary(**corpus_payload.get("summary_features", {})),
            summary_constraints=StatsSummary(**corpus_payload.get("summary_constraints", {})),
            summary_depth=StatsSummary(**corpus_payload.get("summary_depth", {})),
            summary_branching_factor=StatsSummary(**corpus_payload.get("summary_branching_factor", {})),
            summary_configurations=StatsSummary(**corpus_payload.get("summary_configurations", {})),
            features_histogram=[HistogramBucket(**b) for b in corpus_payload.get("features_histogram", [])],
            constraints_histogram=[HistogramBucket(**b) for b in corpus_payload.get("constraints_histogram", [])],
            depth_histogram=[HistogramBucket(**b) for b in corpus_payload.get("depth_histogram", [])],
            configurations_histogram=[HistogramBucket(**b) for b in corpus_payload.get("configurations_histogram", [])],
            constraint_types=[tuple(t) for t in corpus_payload.get("constraint_types", [])],
            group_types=[tuple(t) for t in corpus_payload.get("group_types", [])],
            feature_classification=[tuple(t) for t in corpus_payload.get("feature_classification", [])],
            top_by_features=rows("top_by_features", corpus_payload),
            top_by_constraints=rows("top_by_constraints", corpus_payload),
            top_by_configurations=rows("top_by_configurations", corpus_payload),
        )

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
            corpus=corpus,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Module-level helpers (kept out of the class because they don't need state)
# ─────────────────────────────────────────────────────────────────────────────


def _sum(rows, attr: str) -> int:
    return sum(getattr(r, attr) or 0 for r in rows)


def _summarize(values: list[float | int]) -> StatsSummary:
    """Five-number summary + mean/stddev. Tolerates short/empty inputs."""
    if not values:
        return StatsSummary()
    s = sorted(float(v) for v in values)
    n = len(s)
    mean = sum(s) / n
    sd = stdev(s) if n > 1 else 0.0
    if n >= 4:
        q1, q2, q3 = quantiles(s, n=4)
        # `quantiles` doesn't expose p90 directly; compute it from a 10-quantile.
        deciles = quantiles(s, n=10)
        p90 = deciles[8]
    else:
        q1 = s[0]
        q2 = median(s)
        q3 = s[-1]
        p90 = s[-1]
    return StatsSummary(
        count=n,
        min=s[0],
        q1=round(q1, 3),
        median=round(q2, 3),
        q3=round(q3, 3),
        p90=round(p90, 3),
        max=s[-1],
        mean=round(mean, 3),
        stddev=round(sd, 3),
    )


def _bucket(values: list[int | float], buckets: list[tuple[str, int, int | None]]) -> list[HistogramBucket]:
    """Bucket values into half-open ranges `[lo, hi)`. `hi=None` ⇒ open-ended."""
    out = [HistogramBucket(label=label, count=0) for label, _, _ in buckets]
    for v in values:
        for i, (_, lo, hi) in enumerate(buckets):
            if v >= lo and (hi is None or v < hi):
                out[i].count += 1
                break
    return out


def _linear_bucket(values: list[int | float], max_bucket: int) -> list[HistogramBucket]:
    """One bucket per integer up to `max_bucket`, plus a `≥max_bucket` bin."""
    out = [HistogramBucket(label=str(i), count=0) for i in range(max_bucket)]
    out.append(HistogramBucket(label=f"≥{max_bucket}", count=0))
    for v in values:
        idx = int(v)
        if idx < 0:
            continue
        if idx >= max_bucket:
            out[max_bucket].count += 1
        else:
            out[idx].count += 1
    return out
