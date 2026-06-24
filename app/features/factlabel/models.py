from datetime import datetime

import pytz

from app import db


class HubfileMetrics(db.Model):
    """Materialised fact-label metrics for a hubfile.

    This is UVL-domain data (one row per analysed hubfile, every numeric column
    extracted from the fact label), so it lives in the factlabel domain rather
    than in the generic hubfile feature. The table name is kept as
    ``hubfile_metrics`` and it still references ``hubfiles.id``: the domain
    annotates the generic file, never the other way around.

    The fact label JSON is ~80 KB per file and contains 60+ nested entries.
    Parsing it on every dashboard request would be O(n_hubfiles) work for what
    are simple aggregates (sum, mean, percentiles), so we extract once into
    typed columns and let SQL do the heavy lifting. The row is upserted by
    ``compute_factlabel`` after a successful full (non-light) fact label run.
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
