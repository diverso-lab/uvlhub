"""Extract typed metrics from a fmfactlabel JSON payload.

The fact label JSON is a list-of-dicts shape under three sections
(`metadata`, `metrics`, `analysis`). Each entry is keyed by a human-readable
`name` like "Cross-tree constraints" and carries one of `size`, `value`, or
`ratio` depending on the metric. We translate that into a flat dict whose
keys map 1:1 to columns on `HubfileMetrics`, ready to feed into a row.

Keeping this as a pure function (no DB, no Flask) makes it trivially
testable and lets the backfill command process payloads from anywhere.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Mapping

logger = logging.getLogger(__name__)

# Bumped whenever the extraction logic changes meaningfully; lets backfills
# detect rows that need re-processing without re-running fmfactlabel itself.
EXTRACTOR_VERSION = "1"

# ── Mapping declarations ────────────────────────────────────────────────────
# `(json_section, json_name)` → column name on HubfileMetrics, with the
# extractor used to pull a number out of the entry.
#
# Entries fmfactlabel exposes as a list of features carry their count in the
# `size` field; entries that are intrinsically a number (e.g. "Branching
# factor") carry it in `value`. Percentages like "Total variability" arrive as
# strings ("2.35%") and need parsing. We split the table by extractor type so
# the dispatch stays declarative.

_SIZE_MAP: dict[tuple[str, str], str] = {
    # ── metrics: features ────────────────────────────────────────────────
    ("metrics", "Features"): "features",
    ("metrics", "Abstract features"): "abstract_features",
    ("metrics", "Concrete features"): "concrete_features",
    ("metrics", "Leaf features"): "leaf_features",
    ("metrics", "Compound features"): "compound_features",
    ("metrics", "Top features"): "top_features",
    ("metrics", "Solitary features"): "solitary_features",
    ("metrics", "Grouped features"): "grouped_features",
    ("metrics", "Typed features"): "typed_features",
    ("metrics", "Multi-features"): "multi_features",
    # ── metrics: relationships ───────────────────────────────────────────
    ("metrics", "Tree relationships"): "tree_relationships",
    ("metrics", "Mandatory features"): "mandatory_features",
    ("metrics", "Optional features"): "optional_features",
    ("metrics", "Feature groups"): "feature_groups",
    ("metrics", "Alternative groups"): "alternative_groups",
    ("metrics", "Or groups"): "or_groups",
    ("metrics", "Mutex groups"): "mutex_groups",
    ("metrics", "Cardinality groups"): "cardinality_groups",
    # ── metrics: constraints ─────────────────────────────────────────────
    ("metrics", "Cross-tree constraints"): "cross_tree_constraints",
    ("metrics", "Logical constraints"): "logical_constraints",
    ("metrics", "Simple constraints"): "simple_constraints",
    ("metrics", "Requires constraints"): "requires_constraints",
    ("metrics", "Excludes constraints"): "excludes_constraints",
    ("metrics", "Complex constraints"): "complex_constraints",
    ("metrics", "Pseudo-complex constraints"): "pseudo_complex_constraints",
    ("metrics", "Strict-complex constraints"): "strict_complex_constraints",
    ("metrics", "Arithmetic constraints"): "arithmetic_constraints",
    ("metrics", "Aggregation constraints"): "aggregation_constraints",
    ("metrics", "Features in constraints"): "features_in_constraints",
    # ── analysis: feature classification ─────────────────────────────────
    ("analysis", "Core features"): "core_features",
    ("analysis", "False-optional features"): "false_optional_features",
    ("analysis", "Dead features"): "dead_features",
    ("analysis", "Variant features"): "variant_features",
    ("analysis", "Unique features"): "unique_features",
    ("analysis", "Pure optional features"): "pure_optional_features",
}

_VALUE_MAP: dict[tuple[str, str], str] = {
    # Tree shape — `value` is already numeric.
    ("metrics", "Depth of tree"): "depth_of_tree",
    ("metrics", "Mean depth of tree"): "mean_depth_of_tree",
    ("metrics", "Branching factor"): "branching_factor",
    ("metrics", "Min children per feature"): "min_children_per_feature",
    ("metrics", "Max children per feature"): "max_children_per_feature",
    ("metrics", "Avg children per feature"): "avg_children_per_feature",
    # Constraint averages.
    ("metrics", "Avg features per constraint"): "avg_features_per_constraint",
    ("metrics", "Avg constraints per feature"): "avg_constraints_per_feature",
    # Configuration distribution.
    ("analysis", "Mean"): "cfg_mean_features",
    ("analysis", "Standard deviation"): "cfg_stddev_features",
    ("analysis", "Median"): "cfg_median_features",
    ("analysis", "Min"): "cfg_min_features",
    ("analysis", "Max"): "cfg_max_features",
}

# Percentage strings → float in [0, 1].
_PERCENT_MAP: dict[tuple[str, str], str] = {
    ("analysis", "Total variability"): "total_variability",
    ("analysis", "Partial variability"): "partial_variability",
    ("analysis", "Homogeneity"): "homogeneity",
}

_PERCENT_RE = re.compile(r"^\s*([\d.,]+)\s*%\s*$")
_CONFIG_RE = re.compile(r"^\s*(<=)?\s*([\d.,eE+]+)\s*$")


def _to_int(x: Any) -> int | None:
    if x is None:
        return None
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def _to_float(x: Any) -> float | None:
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _parse_percent(raw: Any) -> float | None:
    """'2.35%' → 0.0235; numeric inputs are passed through as floats."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        m = _PERCENT_RE.match(raw)
        if m:
            return float(m.group(1).replace(",", ".")) / 100.0
        try:
            return float(raw.replace(",", "."))
        except ValueError:
            return None
    return None


def _parse_configurations(raw: Any) -> tuple[float | None, bool | None]:
    """fmfactlabel reports either an exact integer or a string like '<= 1234'.

    Returns ``(value, is_upper_bound)`` as a float because real feature models
    routinely produce 2^N-scale counts (e.g. 1.27e30) that overflow BIGINT.
    Both are None when the analysis was skipped (e.g. light fact label) or
    the value can't be parsed.
    """
    if raw is None:
        return None, None
    if isinstance(raw, (int, float)):
        return float(raw), False
    if isinstance(raw, str):
        m = _CONFIG_RE.match(raw)
        if m:
            try:
                return float(m.group(2).replace(",", ".")), m.group(1) == "<="
            except (TypeError, ValueError):
                return None, None
    return None, None


def _parse_satisfiable(raw: Any) -> bool | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        v = raw.strip().lower()
        if v in {"yes", "true", "1", "satisfiable", "valid"}:
            return True
        if v in {"no", "false", "0", "unsatisfiable", "invalid"}:
            return False
    return None


def _index(payload: Mapping[str, Any], section: str) -> dict[str, dict]:
    """Return a `{name: entry}` dict for a section, tolerating absences.

    fmfactlabel ships its sections as ordered lists rather than dicts, so we
    flatten by `name` to enable O(1) lookup.
    """
    section_data = payload.get(section) or []
    if not isinstance(section_data, list):
        return {}
    return {entry.get("name", ""): entry for entry in section_data if isinstance(entry, dict)}


def extract_metrics(factlabel_json: str | Mapping[str, Any] | None) -> dict[str, Any]:
    """Translate a fact label payload into a flat dict keyed by column name.

    Every value is either a typed primitive or None. Missing entries (light
    fact labels skip the semantic section, older fmfactlabel versions may
    rename fields) become None — never raise — so callers can treat the
    result as a partial update without special-casing.

    Always sets ``extractor_version``. Sets ``parse_error`` only when the
    input is structurally invalid (not when individual fields are missing).
    """
    out: dict[str, Any] = {"extractor_version": EXTRACTOR_VERSION, "parse_error": None}

    if factlabel_json is None or factlabel_json == "":
        out["parse_error"] = "empty payload"
        return out

    if isinstance(factlabel_json, str):
        try:
            payload = json.loads(factlabel_json)
        except (ValueError, TypeError) as e:
            out["parse_error"] = f"json decode failed: {e}"
            return out
    else:
        payload = factlabel_json

    if not isinstance(payload, Mapping):
        out["parse_error"] = f"unexpected payload type: {type(payload).__name__}"
        return out

    metrics_idx = _index(payload, "metrics")
    analysis_idx = _index(payload, "analysis")
    indices = {"metrics": metrics_idx, "analysis": analysis_idx}

    # Size-based extractions (lists of features → count).
    for (section, name), column in _SIZE_MAP.items():
        entry = indices[section].get(name)
        if entry is not None:
            out[column] = _to_int(entry.get("size"))

    # Value-based extractions (already numeric).
    for (section, name), column in _VALUE_MAP.items():
        entry = indices[section].get(name)
        if entry is None:
            continue
        raw = entry.get("value")
        # Some `value` fields are floats (Branching factor: 3.0), some are
        # ints (Depth of tree: 2). We always store as float for *_factor /
        # mean_* / avg_*; everything else as int.
        if column in {
            "depth_of_tree",
            "min_children_per_feature",
            "max_children_per_feature",
            "cfg_min_features",
            "cfg_max_features",
        }:
            out[column] = _to_int(raw)
        else:
            out[column] = _to_float(raw)

    # Percentages → fractions in [0, 1].
    for (section, name), column in _PERCENT_MAP.items():
        entry = indices[section].get(name)
        if entry is not None:
            out[column] = _parse_percent(entry.get("value"))

    # Special: satisfiability + configurations live in `analysis` and need
    # their own parsers because the JSON encodes them oddly.
    sat_entry = analysis_idx.get("Satisfiable (valid)")
    if sat_entry is not None:
        out["satisfiable"] = _parse_satisfiable(sat_entry.get("value"))

    cfg_entry = analysis_idx.get("Configurations")
    if cfg_entry is not None:
        cfg_value, cfg_bound = _parse_configurations(cfg_entry.get("value"))
        out["configurations"] = cfg_value
        out["configurations_is_upper_bound"] = cfg_bound

    return out
