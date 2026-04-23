import logging
import os
from datetime import datetime

import pytz
from dotenv import load_dotenv
from flask import url_for
from sqlalchemy import Text, event
from sqlalchemy.orm import joinedload, object_session

from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet
from core.managers.task_queue_manager import TaskQueueManager

logger = logging.getLogger(__name__)
load_dotenv()


class Hubfile(db.Model):
    __tablename__ = "hubfiles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    checksum = db.Column(db.String(120), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    feature_model_id = db.Column(db.Integer, db.ForeignKey("feature_model.id"), nullable=False)

    feature_model = db.relationship("FeatureModel", back_populates="hubfiles")
    factlabel_json = db.Column(Text, nullable=True)

    def get_formatted_size(self):
        from app.modules.dataset.services import SizeService

        return SizeService().get_human_readable_size(self.size)

    def get_owner_user(self) -> User:
        from app.modules.hubfile.services import HubfileService

        return HubfileService().get_owner_user_by_hubfile(self)

    def get_dataset(self) -> DataSet:
        from app.modules.hubfile.services import HubfileService

        return HubfileService().get_dataset_by_hubfile(self)

    def get_path(self) -> str:
        from app.modules.hubfile.services import HubfileService

        return HubfileService().get_path_by_hubfile(self)

    def get_url(self) -> str:
        from app.modules.hubfile.services import HubfileService

        return HubfileService().get_hubfile_url(self)

    def get_full_path(self) -> str:
        return os.path.join(
            os.getenv("WORKING_DIR", ""),
            "uploads",
            f"user_{self.feature_model.dataset.user_id}",
            f"dataset_{self.feature_model.dataset_id}",
            "uvl",
            self.name,
        )

    def _public_raw_url(self) -> str:
        """Build the public raw-UVL URL for this hubfile (https outside local).

        Shared between the Flamapy IDE and FactLabel helpers so a future
        tweak (e.g. hostname rewrite) only needs to happen in one place.
        """
        from urllib.parse import quote

        raw_url = url_for("hubfile.raw_uvl", file_id=self.id, filename=self.name, _external=True)
        if "localhost" not in raw_url and "127.0.0.1" not in raw_url:
            raw_url = raw_url.replace("http://", "https://", 1)
        # Percent-encode before injecting into another URL's query string,
        # otherwise a filename containing "&", "#" or "?" would corrupt the
        # outer URL. `safe=""` means even "/" and ":" get encoded — the
        # consumer (FactLabel / IDE) URL-decodes the value before fetching.
        return quote(raw_url, safe="")

    def get_ide_url(self) -> str:
        """Return the URL that opens this hubfile in Flamapy IDE."""
        return f"https://ide.flamapy.org/?import={self._public_raw_url()}"

    def get_factlabel_url(self) -> str:
        """Return the URL that opens this hubfile in FactLabel.

        Note: we deliberately don't pass `?v=<version>`. FactLabel's JS
        compares the URL's `v` against its own version.json and redirects
        to /error_version.html (which is a 404 on GitHub Pages) when they
        don't match. Hardcoding `v=1.8.0` here broke as soon as FactLabel
        bumped to 1.8.1. Omitting the param skips the check entirely and
        lets FactLabel pick up whatever version it's currently serving.
        """
        return f"https://fmfactlabel.github.io/app/?file={self._public_raw_url()}"

    def to_dict(self):
        from flask import url_for

        return {
            "id": self.id,
            "name": self.name,
            "checksum": self.checksum,
            "size_in_bytes": self.size,
            "size_in_human_format": self.get_formatted_size(),
            "url": url_for("hubfile.download_file", file_id=self.id, _external=True),
        }

    def __repr__(self):
        return f"<Hubfile id={self.id}, name={self.name}>"


class HubfileMetrics(db.Model):
    """Materialised metrics extracted from `Hubfile.factlabel_json`.

    The fact label JSON is ~80 KB per file and contains 60+ nested entries.
    Parsing it on every dashboard request would be O(n_hubfiles) work for what
    are simple aggregates (sum, mean, percentiles), so we extract once into
    typed columns and let SQL do the heavy lifting. The row is upserted by
    `compute_factlabel` after a successful full (non-light) fact label run.
    """

    __tablename__ = "hubfile_metrics"

    hubfile_id = db.Column(db.Integer, db.ForeignKey("hubfiles.id", ondelete="CASCADE"), primary_key=True)

    # Provenance — lets backfills be reproducible and lets us re-extract when
    # the fmfactlabel schema changes without re-running the (expensive) FM
    # analysis itself.
    extracted_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.utc))
    extractor_version = db.Column(db.String(20), nullable=False)
    parse_error = db.Column(db.Text, nullable=True)

    # ── Structural metrics (counts) ───────────────────────────────────────
    features = db.Column(db.Integer)
    abstract_features = db.Column(db.Integer)
    concrete_features = db.Column(db.Integer)
    leaf_features = db.Column(db.Integer)
    compound_features = db.Column(db.Integer)
    top_features = db.Column(db.Integer)
    solitary_features = db.Column(db.Integer)
    grouped_features = db.Column(db.Integer)
    typed_features = db.Column(db.Integer)
    multi_features = db.Column(db.Integer)

    tree_relationships = db.Column(db.Integer)
    mandatory_features = db.Column(db.Integer)
    optional_features = db.Column(db.Integer)
    feature_groups = db.Column(db.Integer)
    alternative_groups = db.Column(db.Integer)
    or_groups = db.Column(db.Integer)
    mutex_groups = db.Column(db.Integer)
    cardinality_groups = db.Column(db.Integer)

    depth_of_tree = db.Column(db.Integer)
    mean_depth_of_tree = db.Column(db.Float)
    branching_factor = db.Column(db.Float)
    min_children_per_feature = db.Column(db.Integer)
    max_children_per_feature = db.Column(db.Integer)
    avg_children_per_feature = db.Column(db.Float)

    cross_tree_constraints = db.Column(db.Integer)
    logical_constraints = db.Column(db.Integer)
    simple_constraints = db.Column(db.Integer)
    requires_constraints = db.Column(db.Integer)
    excludes_constraints = db.Column(db.Integer)
    complex_constraints = db.Column(db.Integer)
    pseudo_complex_constraints = db.Column(db.Integer)
    strict_complex_constraints = db.Column(db.Integer)
    arithmetic_constraints = db.Column(db.Integer)
    aggregation_constraints = db.Column(db.Integer)
    features_in_constraints = db.Column(db.Integer)
    avg_features_per_constraint = db.Column(db.Float)
    avg_constraints_per_feature = db.Column(db.Float)

    # ── Semantic analysis (only present in non-light fact labels) ─────────
    satisfiable = db.Column(db.Boolean, nullable=True)
    core_features = db.Column(db.Integer)
    false_optional_features = db.Column(db.Integer)
    dead_features = db.Column(db.Integer)
    variant_features = db.Column(db.Integer)
    unique_features = db.Column(db.Integer)
    pure_optional_features = db.Column(db.Integer)

    # `configurations` is reported by fmfactlabel as either an exact integer
    # or a string like "<= 1234" when only an upper bound could be computed
    # within the analysis budget. Splitting it lets queries like
    # AVG(configurations) WHERE NOT is_upper_bound be straightforward.
    #
    # Stored as DOUBLE (precision=53) rather than BIGINT because real feature
    # models routinely produce 2^N-scale counts — e.g. a model with 140
    # independent optional features reports 1.27e30 configurations, which
    # overflows signed BIGINT (max ~9.2e18). Double precision covers anything
    # fmfactlabel can compute (up to ~1.8e308) at the cost of ~15 significant
    # digits, which is plenty for histograms and summaries.
    configurations = db.Column(db.Float(precision=53), nullable=True)
    configurations_is_upper_bound = db.Column(db.Boolean, nullable=True)

    # Stored as fractions in [0, 1] (fmfactlabel reports them as percentages).
    total_variability = db.Column(db.Float)
    partial_variability = db.Column(db.Float)
    homogeneity = db.Column(db.Float)

    cfg_mean_features = db.Column(db.Float)
    cfg_stddev_features = db.Column(db.Float)
    cfg_median_features = db.Column(db.Float)
    cfg_min_features = db.Column(db.Integer)
    cfg_max_features = db.Column(db.Integer)

    hubfile = db.relationship(
        "Hubfile",
        backref=db.backref("metrics", uselist=False, cascade="all, delete-orphan"),
    )

    def __repr__(self):
        return f"<HubfileMetrics hubfile_id={self.hubfile_id} features={self.features}>"


class HubfileViewRecord(db.Model):
    __tablename__ = "hubfile_view_record"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey("hubfiles.id"), nullable=False)
    view_date = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    view_cookie = db.Column(db.String(36))

    def __repr__(self):
        return f"<HubfileViewRecord id={self.id} file_id={self.file_id}>"


class HubfileDownloadRecord(db.Model):
    __tablename__ = "hubfile_download_record"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey("hubfiles.id"), nullable=False)
    download_date = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc), nullable=False)
    download_cookie = db.Column(db.String(36), nullable=False)

    def __repr__(self):
        return f"<HubfileDownloadRecord id={self.id} file_id={self.file_id} date={self.download_date}>"


@event.listens_for(Hubfile, "after_insert")
def hubfile_after_insert_listener(mapper, connection, target):
    session = object_session(target)

    hubfile_with_fm = (
        session.query(Hubfile).options(joinedload(Hubfile.feature_model)).filter(Hubfile.id == target.id).first()
    )
    path = hubfile_with_fm.get_full_path()

    task_manager = TaskQueueManager()

    # UVL transformation
    task_manager.enqueue_task("app.modules.hubfile.tasks.transform_uvl", path=path, timeout=5)

    # Fact Label
    task_manager.enqueue_task("app.modules.hubfile.tasks.compute_factlabel", hubfile_id=target.id, timeout=5)

    # Fact Label (light)
    task_manager.enqueue_task(
        "app.modules.hubfile.tasks.compute_factlabel", hubfile_id=target.id, light_fact_label=True, timeout=5
    )
