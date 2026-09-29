"""Wizard logic for the random feature-model generator.

Per-step form validators, session-state (de)serialisation and the param-dict
builders. Pure functions plus Flask-session helpers, kept out of the route
handlers so the routes stay thin.
"""

import logging
from dataclasses import dataclass, field

from flamapy.metamodels.fm_generator.models import FmgeneratorModel
from flamapy.metamodels.fm_generator.operations import GenerateFeatureModel
from flamapy.metamodels.fm_metamodel.models.feature_model import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations.uvl_writer import UVLWriter
from flamapy.metamodels.pysat_metamodel.operations.pysat_satisfiable import PySATSatisfiable
from flamapy.metamodels.pysat_metamodel.transformations.fm_to_pysat import FmToPysat
from flask import session

logger = logging.getLogger(__name__)

TOTAL_STEPS = 6

SAT_MAX_ATTEMPTS = 20


class SatisfiableModelGenerationError(RuntimeError):
    def __init__(self, model_number: int, attempts: int) -> None:
        self.model_number = model_number
        self.attempts = attempts
        super().__init__(f"No satisfiable model found for model {model_number} " f"after {attempts} attempts.")


# ─── Wizard configuration values ─────────────────────────────────────────

step2_checkbox_fields = [
    "arithmetic_level",
    "type_level",
    "feature_cardinality",
    "aggregate_functions",
    "string_constraints",
    "group_cardinality",
]

step5_checkbox_fields = ["random_attributes"]

step6_checkbox_fields = [
    "ensure_satisfiable",
    "feature_count_suffix",
    "constraint_count_suffix",
]

STEP4_UI_DEFAULTS = {
    # Arithmetic (without aggregates)
    "prob_plus": 0.7,
    "prob_minus": 0.2,
    "prob_times": 0.1,
    "prob_div": 0.0,
    "prob_sum": 0.0,
    "prob_avg": 0.0,
    # Comparison
    "prob_eq": 0.1,
    "prob_lt": 0.2,
    "prob_gt": 0.7,
    "prob_leq": 0.0,
    "prob_geq": 0.0,
    # String constraints
    "prob_len": 0.7,
}


@dataclass
class WizardRouteResult:
    template: str | None = None
    context: dict = field(default_factory=dict)
    redirect_endpoint: str | None = None


# ─── Wizard form value builders ──────────────────────────────────────────


def first_or_value(value, default):
    if isinstance(value, (list, tuple)):
        return value[0] if value else default
    if value is None:
        return default
    return value


def build_step1_values(params_dict):
    return {
        "num_models_val": params_dict.get("NUM_MODELS", 5),
        "seed": params_dict.get("SEED", 42),
        "name_prefix": params_dict.get("NAME_PREFIX", ""),
    }


def build_step2_values(params_dict):
    return {
        "boolean_level": True,
        "arithmetic_level": params_dict.get("ARITHMETIC_LEVEL", False),
        "type_level": params_dict.get("TYPE_LEVEL", False),
        "feature_cardinality": params_dict.get("FEATURE_CARDINALITY", False),
        "aggregate_functions": params_dict.get("AGGREGATE_FUNCTIONS", False),
        "string_constraints": params_dict.get("STRING_CONSTRAINTS", False),
        "group_cardinality": params_dict.get("GROUP_CARDINALITY", False),
    }


def build_step3_values(params_dict):
    return {
        "num_features_min": params_dict.get("MIN_FEATURES", 10),
        "num_features_max": params_dict.get("MAX_FEATURES", 50),
        "max_tree_depth": params_dict.get("MAX_TREE_DEPTH", 5),
        "dist_boolean": params_dict.get(
            "FEATURE_DIST_BOOLEAN",
            0.7,
        ),
        "dist_integer": params_dict.get(
            "FEATURE_DIST_INTEGER",
            0.1,
        ),
        "dist_real": params_dict.get(
            "FEATURE_DIST_REAL",
            0.1,
        ),
        "dist_string": params_dict.get(
            "FEATURE_DIST_STRING",
            0.1,
        ),
        "dist_optional": params_dict.get("DIST_OPTIONAL", 0.3),
        "dist_mandatory": params_dict.get("DIST_MANDATORY", 0.3),
        "dist_alternative": params_dict.get("DIST_ALTERNATIVE", 0.2),
        "dist_or": params_dict.get("DIST_OR", 0.2),
        "dist_group_cardinality": params_dict.get("DIST_GROUP_CARDINALITY", 0.0),
        "group_cardinality_min": params_dict.get("GROUP_CARDINALITY_MIN", 1),
        "group_cardinality_max": params_dict.get("GROUP_CARDINALITY_MAX", 6),
        "prob_fc": params_dict.get("PROB_FEATURE_CARDINALITY", 0.1),
        "min_feature_cardinality": first_or_value(params_dict.get("MIN_FEATURE_CARDINALITY"), 2),
        "max_feature_cardinality": first_or_value(params_dict.get("MAX_FEATURE_CARDINALITY"), 5),
        "arithmetic_level": params_dict.get("ARITHMETIC_LEVEL", False),
        "type_level": params_dict.get("TYPE_LEVEL", False),
        "feature_cardinality": params_dict.get("FEATURE_CARDINALITY", False),
        "aggregate_functions": params_dict.get("AGGREGATE_FUNCTIONS", False),
        "string_constraints": params_dict.get("STRING_CONSTRAINTS", False),
        "group_cardinality": params_dict.get("GROUP_CARDINALITY", False),
        "rel_dist_total": "1.0000",
    }


def build_step4_values(params_dict):
    wizard = session.get("wizard", {})
    has_saved = "4" in wizard
    max_feats = int(params_dict.get("MAX_FEATURES", 1000))

    try:
        ecr_default = max(1, int(float(params_dict.get("EXTRA_CONSTRAINT_REPRESENTATIVENESS", 1))))
    except (TypeError, ValueError):
        ecr_default = 1

    defaults = {
        "num_constraints_min": params_dict.get("MIN_CONSTRAINTS", 1),
        "num_constraints_max": params_dict.get("MAX_CONSTRAINTS", 10),
        "extra_constraint_repr": ecr_default,
        "vars_per_ctc_min": params_dict.get("MIN_VARS_PER_CONSTRAINT", 1),
        "vars_per_ctc_max": min(int(params_dict.get("MAX_VARS_PER_CONSTRAINT", 10)), max_feats),
        "max_features": max_feats,
        "boolop_sum": "1.0000",
        "arithmetic_sum": "1.0000",
        "cmp_sum": "1.0000",
        "ctc_dist_sum": "1.0000",
        "ctc_dist_boolean": params_dict.get("CTC_DIST_BOOLEAN", 0.7),
        "ctc_dist_integer": params_dict.get("CTC_DIST_INTEGER", 0.2),
        "ctc_dist_real": params_dict.get("CTC_DIST_REAL", 0.1),
        "ctc_dist_string": params_dict.get("CTC_DIST_STRING", 0.0),
        "arithmetic_level": params_dict.get("ARITHMETIC_LEVEL", False),
        "aggregate_functions": params_dict.get("AGGREGATE_FUNCTIONS", False),
        "type_level": params_dict.get("TYPE_LEVEL", False),
        "string_constraints": params_dict.get("STRING_CONSTRAINTS", False),
        "prob_not": params_dict.get("PROB_NOT", 0.3),
        "prob_and": params_dict.get("PROB_AND", 0.7),
        "prob_or": params_dict.get("PROB_OR_CT", 0.1),
        "prob_implies": params_dict.get("PROB_IMPLICATION", 0.1),
        "prob_equiv": params_dict.get("PROB_EQUIVALENCE", 0.1),
    }

    if has_saved:
        defaults.update(
            {
                "prob_plus": params_dict.get("PROB_SUM", STEP4_UI_DEFAULTS["prob_plus"]),
                "prob_minus": params_dict.get("PROB_SUBSTRACT", STEP4_UI_DEFAULTS["prob_minus"]),
                "prob_times": params_dict.get("PROB_MULTIPLY", STEP4_UI_DEFAULTS["prob_times"]),
                "prob_div": params_dict.get("PROB_DIVIDE", STEP4_UI_DEFAULTS["prob_div"]),
                "prob_sum": params_dict.get("PROB_SUM_FUNCTION", STEP4_UI_DEFAULTS["prob_sum"]),
                "prob_avg": params_dict.get("PROB_AVG_FUNCTION", STEP4_UI_DEFAULTS["prob_avg"]),
                "prob_eq": params_dict.get("PROB_EQUALS", STEP4_UI_DEFAULTS["prob_eq"]),
                "prob_lt": params_dict.get("PROB_LESS", STEP4_UI_DEFAULTS["prob_lt"]),
                "prob_gt": params_dict.get("PROB_GREATER", STEP4_UI_DEFAULTS["prob_gt"]),
                "prob_leq": params_dict.get("PROB_LESS_EQUALS", STEP4_UI_DEFAULTS["prob_leq"]),
                "prob_geq": params_dict.get("PROB_GREATER_EQUALS", STEP4_UI_DEFAULTS["prob_geq"]),
                "prob_len": (
                    params_dict.get("PROB_LEN_FUNCTION", STEP4_UI_DEFAULTS["prob_len"])
                    if params_dict.get("TYPE_LEVEL") and params_dict.get("STRING_CONSTRAINTS")
                    else 0.0
                ),
            }
        )
    else:
        defaults.update(STEP4_UI_DEFAULTS)
        if not (params_dict.get("TYPE_LEVEL") and params_dict.get("STRING_CONSTRAINTS")):
            defaults["prob_len"] = 0.0

    values = load_step_state(4, defaults)
    values["arithmetic_level"] = params_dict.get("ARITHMETIC_LEVEL", False)
    values["aggregate_functions"] = params_dict.get("AGGREGATE_FUNCTIONS", False)
    values["type_level"] = params_dict.get("TYPE_LEVEL", False)
    values["string_constraints"] = params_dict.get("STRING_CONSTRAINTS", False)

    try:
        values["vars_per_ctc_max"] = str(min(int(values.get("vars_per_ctc_max", max_feats)), max_feats))
    except Exception:
        values["vars_per_ctc_max"] = str(max_feats)

    values["max_features"] = max_feats
    return values


def build_step5_values(params_dict):
    defaults = {
        "random_attributes": params_dict.get("RANDOM_ATTRIBUTES", True),
        "min_attributes": params_dict.get("MIN_ATTRIBUTES", 1),
        "max_attributes": params_dict.get("MAX_ATTRIBUTES", 5),
        "attributes_list": params_dict.get("ATTRIBUTES_LIST", []),
        "dist_boolean_atr": params_dict.get("ATTR_DIST_BOOLEAN", 0.7),
        "dist_integer_atr": params_dict.get("ATTR_DIST_INTEGER", 0.1),
        "dist_real_atr": params_dict.get("ATTR_DIST_REAL", 0.1),
        "dist_string_atr": params_dict.get("ATTR_DIST_STRING", 0.1),
        "attr_dist_sum": "1.0000",
    }

    return load_step_state(5, defaults)


def build_step6_values(params_dict):
    defaults = {
        "ensure_satisfiable": params_dict.get("ENSURE_SATISFIABLE", False),
        "feature_count_suffix": params_dict.get("INCLUDE_FEATURE_COUNT_SUFFIX", False),
        "constraint_count_suffix": params_dict.get("INCLUDE_CONSTRAINT_COUNT_SUFFIX", False),
    }
    return load_step_state(6, defaults)


# ─── Validators ───────────────────────────────────────────────────────────


def validate_step1_form(form):
    """Step 1 — batch. num_models + seed + name_prefix."""
    errors, values = {}, {}

    num_models_val = form.get("num_models_val", "").strip()
    try:
        num_models = int(num_models_val)
        if num_models < 1:
            errors["num_models_val"] = "Number of models must be at least 1."
        elif num_models > 1000:
            errors["num_models_val"] = "Number of models cannot exceed 1000."
    except Exception:
        errors["num_models_val"] = "Number of models must be an integer."

    seed_val = form.get("seed", "").strip()
    try:
        seed = int(seed_val)
        if seed <= 0:
            errors["seed"] = "Seed must be a positive integer."
    except Exception:
        errors["seed"] = "Seed must be a positive integer."

    for k in form:
        values[k] = form[k]
    return errors, values


def validate_step2_form(form):
    """Step 2 — language levels. All checkboxes; nothing to numerically
    validate. We simply enforce that minor levels are only on if their
    major is on (the engine does this too, but failing fast here keeps
    the UI honest)."""
    errors, values = {}, {}
    arith = "arithmetic_level" in form
    type_ = "type_level" in form
    feat_card = "feature_cardinality" in form
    aggregate = "aggregate_functions" in form
    string_ctc = "string_constraints" in form
    group_card = "group_cardinality" in form

    if feat_card and not arith:
        errors["feature_cardinality"] = "Requires Arithmetic level."
    if aggregate and not arith:
        errors["aggregate_functions"] = "Requires Arithmetic level."
    if string_ctc and not type_:
        errors["string_constraints"] = "Requires Type level."

    values.update(
        {
            "arithmetic_level": arith,
            "type_level": type_,
            "feature_cardinality": feat_card,
            "aggregate_functions": aggregate,
            "string_constraints": string_ctc,
            "group_cardinality": group_card,
        }
    )
    return errors, values


def validate_step3_form(form, params_dict=None):
    """Step 3 — feature tree. min/max features, depth, rel dist, and the
    feat/group cardinality blocks.

    `params_dict` carries the level flags decided in step 2. If omitted,
    we fall back to reading a hidden input from the form."""
    params_dict = params_dict or {}
    errors, values = {}, {}

    # Features
    try:
        min_features = int(form.get("num_features_min", "").strip())
        if min_features < 1:
            errors["num_features_min"] = "Min. features must be at least 1."
    except Exception:
        min_features = None
        errors["num_features_min"] = "Min. features must be an integer."

    try:
        max_features = int(form.get("num_features_max", "").strip())
        if max_features < 1:
            errors["num_features_max"] = "Max. features must be at least 1."
    except Exception:
        max_features = None
        errors["num_features_max"] = "Max. features must be an integer."

    if (
        "num_features_min" not in errors
        and "num_features_max" not in errors
        and min_features is not None
        and max_features is not None
        and min_features > max_features
    ):
        errors["num_features_max"] = "Max. features must be ≥ Min. features."

    # Tree depth
    try:
        max_tree_depth = int(form.get("max_tree_depth", "").strip())
        if "num_features_max" not in errors and not (1 <= max_tree_depth <= max_features):
            errors["max_tree_depth"] = "Maximum tree depth must be between 1 and Max. features."
    except Exception:
        errors["max_tree_depth"] = "Maximum tree depth must be an integer."

    # Relation distribution (including group cardinality if its toggle is on)
    group_cardinality_enabled = bool(
        params_dict.get("GROUP_CARDINALITY") if "GROUP_CARDINALITY" in params_dict else "group_cardinality" in form
    )
    feature_cardinality_enabled = bool(
        params_dict.get("FEATURE_CARDINALITY")
        if "FEATURE_CARDINALITY" in params_dict
        else "feature_cardinality" in form
    )
    rel_fields = ["dist_optional", "dist_mandatory", "dist_alternative", "dist_or"]
    if group_cardinality_enabled:
        rel_fields.append("dist_group_cardinality")
    rel_values = []
    for f in rel_fields:
        try:
            v = _safe_float(form.get(f, "").strip(), 0.0)
            if not (0.0 <= v <= 1.0):
                errors[f] = "Value must be between 0 and 1."
            rel_values.append(v)
        except Exception:
            errors[f] = "Value must be a decimal between 0 and 1."
            rel_values.append(0.0)
    rel_total = sum(rel_values)
    if abs(rel_total - 1.0) > 0.001:
        for f in rel_fields:
            if f not in errors:
                errors[f] = "The relation-distribution probabilities must sum to 1.0."
        errors["rel_dist_total"] = f"Current sum: {rel_total:.4f}. Must be 1.0."
    values["rel_dist_total"] = f"{rel_total:.4f}"

    # Group cardinality min/max (only when the toggle is on)
    if group_cardinality_enabled:
        try:
            gc_min = int(form.get("group_cardinality_min", "").strip())
            if gc_min < 1:
                errors["group_cardinality_min"] = "Group cardinality min must be at least 1."
        except Exception:
            gc_min = None
            errors["group_cardinality_min"] = "Group cardinality min must be an integer."
        try:
            gc_max = int(form.get("group_cardinality_max", "").strip())
            if "num_features_max" not in errors and max_features and gc_max > max_features:
                errors["group_cardinality_max"] = "Group cardinality max cannot exceed Max. features."
            elif gc_max < 1:
                errors["group_cardinality_max"] = "Group cardinality max must be at least 1."
        except Exception:
            gc_max = None
            errors["group_cardinality_max"] = "Group cardinality max must be an integer."
        if (
            "group_cardinality_min" not in errors
            and "group_cardinality_max" not in errors
            and gc_min is not None
            and gc_max is not None
            and gc_min > gc_max
        ):
            errors["group_cardinality_max"] = "Group cardinality max must be ≥ min."

    # Feature cardinality block (only when the toggle is on in step 2)
    if feature_cardinality_enabled:
        prob_fc_val = form.get("prob_fc")
        if prob_fc_val is not None:
            try:
                ap = _safe_float(prob_fc_val, 0.0)
                if not (0.0 <= ap <= 1.0):
                    errors["prob_fc"] = "Attach probability must be between 0 and 1."
            except Exception:
                errors["prob_fc"] = "Attach probability must be a number between 0 and 1."

    for k in form:
        values[k] = form[k]
    return errors, values


def validate_step4_form(form, max_features: int = 10000, params_dict=None):
    """Step 4 — constraints. Number / vars ranges + all probability
    distributions.

    `params_dict` carries the level flags decided in step 2 (ARITHMETIC_LEVEL,
    TYPE_LEVEL, etc.). If omitted, we fall back to the form (which may also
    carry hidden mirror inputs)."""
    params_dict = params_dict or {}
    errors, values = {}, {}

    # 1) Number of constraints
    try:
        min_constraints = int(form.get("num_constraints_min", "").strip())
        if min_constraints < 1:
            errors["num_constraints_min"] = "Min. constraints must be at least 1."
    except Exception:
        min_constraints = None
        errors["num_constraints_min"] = "Min. constraints must be an integer."
    try:
        max_constraints = int(form.get("num_constraints_max", "").strip())
        if max_constraints < 1:
            errors["num_constraints_max"] = "Max. constraints must be at least 1."
    except Exception:
        max_constraints = None
        errors["num_constraints_max"] = "Max. constraints must be an integer."
    if (
        "num_constraints_min" not in errors
        and "num_constraints_max" not in errors
        and min_constraints is not None
        and max_constraints is not None
        and min_constraints > max_constraints
    ):
        errors["num_constraints_max"] = "Max. constraints must be ≥ Min. constraints."

    # 2) Extra constraint representativeness
    try:
        extra_cr = int(form.get("extra_constraint_repr", "").strip())
    except Exception:
        extra_cr = None
        errors["extra_constraint_repr"] = "Must be an integer."

    # 3) Vars per constraint
    try:
        vpc_max = int(form.get("vars_per_ctc_max", "").strip())
        if vpc_max < 1:
            errors["vars_per_ctc_max"] = "Max. vars per constraint must be at least 1."
    except Exception:
        vpc_max = None
        errors["vars_per_ctc_max"] = "Max. vars per constraint must be an integer."

    if extra_cr is not None and vpc_max is not None:
        if extra_cr < 1:
            errors["extra_constraint_repr"] = "Must be ≥ 1."
        elif extra_cr > vpc_max:
            errors["extra_constraint_repr"] = "Must be ≤ Max. vars per constraint."

    try:
        vpc_min = int(form.get("vars_per_ctc_min", "").strip())
        if vpc_min < 1:
            errors["vars_per_ctc_min"] = "Min. vars per constraint must be at least 1."
    except Exception:
        vpc_min = None
        errors["vars_per_ctc_min"] = "Min. vars per constraint must be an integer."

    if isinstance(vpc_max, int) and vpc_max > max_features:
        errors["vars_per_ctc_max"] = "Max. vars per constraint cannot exceed Max. features."

    if (
        "vars_per_ctc_min" not in errors
        and "vars_per_ctc_max" not in errors
        and vpc_min is not None
        and isinstance(vpc_max, int)
        and vpc_min > vpc_max
    ):
        errors["vars_per_ctc_max"] = "Max. vars per constraint must be ≥ Min."

    # 4) Boolean operators (+ NOT)
    prob_not = _safe_float(form.get("prob_not"), 0.0)
    if not (0.0 <= prob_not <= 1.0):
        errors["prob_not"] = "Value must be between 0 and 1."
    prob_and = _safe_float(form.get("prob_and"), 0.0)
    prob_or = _safe_float(form.get("prob_or"), 0.0)
    prob_implies = _safe_float(form.get("prob_implies"), 0.0)
    prob_equiv = _safe_float(form.get("prob_equiv"), 0.0)
    sum_bool = prob_and + prob_or + prob_implies + prob_equiv
    if abs(sum_bool - 1.0) > 0.001:
        for f in ("prob_and", "prob_or", "prob_implies", "prob_equiv"):
            if f not in errors:
                errors[f] = "The boolean-connective probabilities must sum to 1.0."
        errors["boolop_sum"] = f"Current sum: {sum_bool:.4f}. Must be 1.0."
    values["boolop_sum"] = f"{sum_bool:.4f}"

    # 5) Arithmetic (conditional) + comparison (conditional).
    # Prefer params_dict (step 2 truth) over any form mirrors.
    arith_on = (
        params_dict.get("ARITHMETIC_LEVEL")
        if "ARITHMETIC_LEVEL" in params_dict
        else form.get("arithmetic_level") in ("on", "true", "1", True)
    )
    agg_on = (
        params_dict.get("AGGREGATE_FUNCTIONS")
        if "AGGREGATE_FUNCTIONS" in params_dict
        else form.get("aggregate_functions") in ("on", "true", "1", True)
    )
    if arith_on:
        prob_plus = _safe_float(form.get("prob_plus"), 0.0)
        prob_minus = _safe_float(form.get("prob_minus"), 0.0)
        prob_times = _safe_float(form.get("prob_times"), 0.0)
        prob_div = _safe_float(form.get("prob_div"), 0.0)
        arith_sum = prob_plus + prob_minus + prob_times + prob_div
        fields = ["prob_plus", "prob_minus", "prob_times", "prob_div"]
        if agg_on:
            prob_sum = _safe_float(form.get("prob_sum"), 0.0)
            prob_avg = _safe_float(form.get("prob_avg"), 0.0)
            arith_sum += prob_sum + prob_avg
            fields += ["prob_sum", "prob_avg"]
        if abs(arith_sum - 1.0) > 0.001:
            for f in fields:
                if f not in errors:
                    errors[f] = "Arithmetic-level probabilities{} must sum to 1.0.".format(
                        " (including aggregates)" if agg_on else ""
                    )
            errors["arithmetic_sum"] = f"Current sum: {arith_sum:.4f}. Must be 1.0."
        values["arithmetic_sum"] = f"{arith_sum:.4f}"

        prob_eq = _safe_float(form.get("prob_eq"), 0.0)
        prob_lt = _safe_float(form.get("prob_lt"), 0.0)
        prob_gt = _safe_float(form.get("prob_gt"), 0.0)
        prob_leq = _safe_float(form.get("prob_leq"), 0.0)
        prob_geq = _safe_float(form.get("prob_geq"), 0.0)
        cmp_sum = prob_eq + prob_lt + prob_gt + prob_leq + prob_geq
        if abs(cmp_sum - 1.0) > 0.001:
            for f in ("prob_eq", "prob_lt", "prob_gt", "prob_leq", "prob_geq"):
                if f not in errors:
                    errors[f] = "Comparison-operator probabilities must sum to 1.0."
            errors["cmp_sum"] = f"Current sum: {cmp_sum:.4f}. Must be 1.0."
        values["cmp_sum"] = f"{cmp_sum:.4f}"
    else:
        values["arithmetic_sum"] = "1.0000"
        values["cmp_sum"] = "1.0000"

    # 6) Type level / string constraints — also from step 2.
    type_on = (
        params_dict.get("TYPE_LEVEL")
        if "TYPE_LEVEL" in params_dict
        else form.get("type_level") in ("on", "true", "1", True)
    )
    str_on = (
        params_dict.get("STRING_CONSTRAINTS")
        if "STRING_CONSTRAINTS" in params_dict
        else form.get("string_constraints") in ("on", "true", "1", True)
    )
    if str_on and type_on:
        prob_len = _safe_float(form.get("prob_len"), 0.0)
        if not (0.0 <= prob_len <= 1.0):
            errors["prob_len"] = "Value must be between 0 and 1."

    # 7) CTC type distribution (CTC_DIST_*)
    if arith_on or type_on:
        ctc_fields = [
            ("ctc_dist_boolean", True),
            ("ctc_dist_integer", arith_on),
            ("ctc_dist_real", arith_on),
            ("ctc_dist_string", type_on and str_on),
        ]
        active = 0.0
        for field_name, is_active in ctc_fields:
            v = _safe_float(form.get(field_name), 0.0)
            if not is_active:
                v = 0.0
            if not (0.0 <= v <= 1.0):
                errors[field_name] = "Value must be between 0 and 1."
            values[field_name] = v
            if is_active:
                active += v
        if abs(active - 1.0) > 0.001:
            errors["ctc_dist_sum"] = f"Current sum: {active:.4f}. Active type probabilities must total 1.0."
        values["ctc_dist_sum"] = f"{active:.4f}"

    for k in form:
        values[k] = form[k]
    return errors, values


def validate_step5_form(form, params_dict=None):
    """Step 5 — attributes. Mirror of the legacy step4 validator."""
    errors, values = {}, {}
    params_dict = params_dict or {}

    arith_on = bool(params_dict.get("ARITHMETIC_LEVEL", False))
    type_on = bool(params_dict.get("TYPE_LEVEL", False))
    str_on = bool(params_dict.get("STRING_CONSTRAINTS", False))

    random_checked = "random_attributes" in form
    values["random_attributes"] = random_checked

    if random_checked:
        try:
            min_attr = int(form.get("min_attributes", "").strip())
            if not (0 <= min_attr <= 1000):
                errors["min_attributes"] = "Min. attributes must be between 0 and 1000."
        except Exception:
            min_attr = None
            errors["min_attributes"] = "Min. attributes must be an integer."
        try:
            max_attr = int(form.get("max_attributes", "").strip())
            if not (0 <= max_attr <= 1000):
                errors["max_attributes"] = "Max. attributes must be between 0 and 1000."
        except Exception:
            max_attr = None
            errors["max_attributes"] = "Max. attributes must be an integer."
        if (
            "min_attributes" not in errors
            and "max_attributes" not in errors
            and min_attr is not None
            and max_attr is not None
            and min_attr > max_attr
        ):
            errors["max_attributes"] = "Max. attributes must be ≥ Min."
        values["min_attributes"] = form.get("min_attributes", "")
        values["max_attributes"] = form.get("max_attributes", "")

        # Attribute-type distribution
        dist_fields = [
            ("dist_boolean_atr", True),
            ("dist_integer_atr", arith_on),
            ("dist_real_atr", arith_on),
            ("dist_string_atr", type_on),
        ]
        active_total = 0.0
        for field_name, is_active in dist_fields:
            v = _safe_float(form.get(field_name), 0.0)
            if not is_active:
                v = 0.0
            if not (0.0 <= v <= 1.0):
                errors[field_name] = "Value must be between 0 and 1."
            values[field_name] = v
            if is_active:
                active_total += v
        if abs(active_total - 1.0) > 0.001:
            errors["attr_dist_sum"] = f"Current sum: {active_total:.4f}. Active type probabilities must total 1.0."
        values["attr_dist_sum"] = f"{active_total:.4f}"
    else:
        values["min_attributes"] = ""
        values["max_attributes"] = ""
        # Manual cards — shape-validate each
        attr_count = 0
        while f"attr_name_{attr_count}" in form:
            attr_count += 1
        for i in range(attr_count):
            name = (form.get(f"attr_name_{i}", "") or "").strip()
            if not name:
                errors[f"attr_name_{i}"] = "Attribute name is required."
            type_lc = (form.get(f"attr_type_{i}", "") or "").strip().lower()
            use_in_ctc = form.get(f"attr_use_in_constraints_{i}") == "on"
            if use_in_ctc:
                if type_lc in ("integer", "real") and not arith_on:
                    errors[f"attr_use_in_constraints_{i}"] = (
                        "Integer/Real attrs can be used in constraints only when Arithmetic level is on."
                    )
                elif type_lc == "string" and not (type_on and str_on):
                    errors[f"attr_use_in_constraints_{i}"] = (
                        "String attrs can be used in constraints only when Type level + String constraints are on."
                    )
            prob = (form.get(f"attr_attach_prob_{i}", "") or "").strip()
            if not prob:
                errors[f"attr_attach_prob_{i}"] = "Attach probability is required."
            else:
                try:
                    p = float(prob)
                    if not (0.0 <= p <= 1.0):
                        errors[f"attr_attach_prob_{i}"] = "Attach probability must be between 0 and 1."
                except Exception:
                    errors[f"attr_attach_prob_{i}"] = "Attach probability must be a number."
            if type_lc == "boolean":
                t_checked = form.get(f"attr_value_true_{i}") is not None
                f_checked = form.get(f"attr_value_false_{i}") is not None
                if not (t_checked or f_checked):
                    errors[f"attr_value_bool_{i}"] = "Select at least one boolean value."
            elif type_lc in ("integer", "real", "string"):
                mn = (form.get(f"attr_min_value_{i}", "") or "").strip()
                mx = (form.get(f"attr_max_value_{i}", "") or "").strip()
                if not mn or not mx:
                    errors[f"attr_minmax_{i}"] = "Min and Max are required."
                else:
                    try:
                        if type_lc == "real":
                            lo, hi = float(mn), float(mx)
                        else:
                            lo, hi = int(mn), int(mx)
                        if type_lc == "string" and (lo < 0 or hi < 0):
                            errors[f"attr_minmax_{i}"] = "Min and Max must be non-negative."
                        elif lo > hi:
                            errors[f"attr_minmax_{i}"] = "Min cannot be greater than Max."
                    except Exception:
                        errors[f"attr_minmax_{i}"] = "Min and Max must be numbers."
        for k in form:
            values[k] = form[k]
    return errors, values


def validate_step6_form(form):
    """Step 6 — output options. Just checkboxes; nothing to fail on."""
    return {}, {
        "ensure_satisfiable": "ensure_satisfiable" in form,
        "feature_count_suffix": "feature_count_suffix" in form,
        "constraint_count_suffix": "constraint_count_suffix" in form,
    }


# ─── Attribute helpers (manual mode) — unchanged semantics ───────────────


def _collect_manual_attributes(form, params_dict):
    attr_count = 0
    while f"attr_name_{attr_count}" in form:
        attr_count += 1

    attributes_data, attach_probs, in_constraints = [], [], []
    for i in range(attr_count):
        name = form.get(f"attr_name_{i}", "")
        t_ = form.get(f"attr_type_{i}", "").strip().lower()
        attach_prob = _safe_float(form.get(f"attr_attach_prob_{i}"), 1.0)
        raw_use = form.get(f"attr_use_in_constraints_{i}") == "on"
        if t_ == "boolean":
            use_in_ctc = raw_use
        elif t_ in ("integer", "real"):
            use_in_ctc = raw_use and params_dict.get("ARITHMETIC_LEVEL", False)
        elif t_ == "string":
            use_in_ctc = (
                raw_use and params_dict.get("TYPE_LEVEL", False) and params_dict.get("STRING_CONSTRAINTS", False)
            )
        else:
            use_in_ctc = False

        if t_ == "boolean":
            values_list = []
            if form.get(f"attr_value_true_{i}") is not None:
                values_list.append(True)
            if form.get(f"attr_value_false_{i}") is not None:
                values_list.append(False)
            attr_dict = {
                "name": name,
                "type": "Boolean",
                "value": values_list,
                "attach_probability": attach_prob,
                "use_in_constraints": use_in_ctc,
            }
        elif t_ in ("integer", "real", "string"):
            attr_dict = {
                "name": name,
                "type": t_.capitalize(),
                "min_value": form.get(f"attr_min_value_{i}", None),
                "max_value": form.get(f"attr_max_value_{i}", None),
                "attach_probability": attach_prob,
                "use_in_constraints": use_in_ctc,
            }
        else:
            continue
        attributes_data.append(attr_dict)
        attach_probs.append(attach_prob)
        in_constraints.append(use_in_ctc)
    return attributes_data, attach_probs, in_constraints


# ─── Step form persistence helpers ───────────────────────────────────────


def _apply_step1_batch(params_dict, form):
    params_dict["NUM_MODELS"] = int(form.get("num_models_val"))
    params_dict["SEED"] = int(form.get("seed"))
    params_dict["NAME_PREFIX"] = form.get("name_prefix", "")


def _apply_step2_levels(params_dict, form):
    """Persist only the level toggles from step 2.

    Normalises the hierarchy so session state matches what
    ``Params.__post_init__`` would produce:
      * TYPE_LEVEL → ARITHMETIC_LEVEL (typed attrs imply arithmetic).
      * Minor levels (feature/aggregate, string) are cleared when their
        major is off.
    """
    # Boolean is the base level — always on once step 2 has been visited,
    # so the summary sidebar always lists "Majors: Boolean, …" from here on.
    params_dict["BOOLEAN_LEVEL"] = True
    params_dict["ARITHMETIC_LEVEL"] = "arithmetic_level" in form
    params_dict["TYPE_LEVEL"] = "type_level" in form
    params_dict["FEATURE_CARDINALITY"] = "feature_cardinality" in form
    params_dict["AGGREGATE_FUNCTIONS"] = "aggregate_functions" in form
    params_dict["STRING_CONSTRAINTS"] = "string_constraints" in form
    params_dict["GROUP_CARDINALITY"] = "group_cardinality" in form
    if params_dict["TYPE_LEVEL"]:
        params_dict["ARITHMETIC_LEVEL"] = True
    if not params_dict["ARITHMETIC_LEVEL"]:
        params_dict["FEATURE_CARDINALITY"] = False
        params_dict["AGGREGATE_FUNCTIONS"] = False
    if not params_dict["TYPE_LEVEL"]:
        params_dict["STRING_CONSTRAINTS"] = False


def _apply_step3_tree(params_dict, form):
    """Persist feature tree + feat/group-cardinality settings from step 3."""
    params_dict["MIN_FEATURES"] = int(form.get("num_features_min", 1))
    params_dict["MAX_FEATURES"] = int(form.get("num_features_max", 10))
    params_dict["MAX_TREE_DEPTH"] = int(form.get("max_tree_depth", 5))
    params_dict["FEATURE_DIST_BOOLEAN"] = _safe_float(
        form.get("dist_boolean"),
        0.7,
    )

    params_dict["FEATURE_DIST_INTEGER"] = _safe_float(
        form.get("dist_integer"),
        0.1,
    )

    params_dict["FEATURE_DIST_REAL"] = _safe_float(
        form.get("dist_real"),
        0.1,
    )

    params_dict["FEATURE_DIST_STRING"] = _safe_float(
        form.get("dist_string"),
        0.1,
    )
    params_dict["DIST_OPTIONAL"] = _safe_float(form.get("dist_optional"), 0.3)
    params_dict["DIST_MANDATORY"] = _safe_float(form.get("dist_mandatory"), 0.3)
    params_dict["DIST_ALTERNATIVE"] = _safe_float(form.get("dist_alternative"), 0.2)
    params_dict["DIST_OR"] = _safe_float(form.get("dist_or"), 0.2)

    if params_dict.get("GROUP_CARDINALITY"):
        params_dict["DIST_GROUP_CARDINALITY"] = _safe_float(form.get("dist_group_cardinality"), 0.0)
        params_dict["GROUP_CARDINALITY_MIN"] = int(form.get("group_cardinality_min", 1))
        params_dict["GROUP_CARDINALITY_MAX"] = int(form.get("group_cardinality_max", 6))
    else:
        params_dict["DIST_GROUP_CARDINALITY"] = 0.0

    if params_dict.get("FEATURE_CARDINALITY"):
        params_dict["PROB_FEATURE_CARDINALITY"] = _safe_float(form.get("prob_fc"), 0.1)
        params_dict["MIN_FEATURE_CARDINALITY"] = [int(form.get("min_feature_cardinality", 2))]
        params_dict["MAX_FEATURE_CARDINALITY"] = [int(form.get("max_feature_cardinality", 5))]
    else:
        params_dict["PROB_FEATURE_CARDINALITY"] = 0.0
        params_dict.pop("MIN_FEATURE_CARDINALITY", None)
        params_dict.pop("MAX_FEATURE_CARDINALITY", None)

    # Renormalise relation distribution so it totals EXACTLY 1.0
    _keys = ["DIST_OPTIONAL", "DIST_MANDATORY", "DIST_ALTERNATIVE", "DIST_OR", "DIST_GROUP_CARDINALITY"]
    total = sum(params_dict[k] for k in _keys)
    if total > 0:
        for k in _keys:
            params_dict[k] = round(params_dict[k] / total, 6)
        params_dict[_keys[-1]] += round(1.0 - sum(params_dict[k] for k in _keys), 6)


def _apply_step4_constraints(params_dict, form):
    """Persist constraint counts + all probability distributions from step 4."""
    params_dict["MIN_CONSTRAINTS"] = int(form.get("num_constraints_min", 1))
    params_dict["MAX_CONSTRAINTS"] = int(form.get("num_constraints_max", 10))
    try:
        params_dict["EXTRA_CONSTRAINT_REPRESENTATIVENESS"] = max(1, int(float(form.get("extra_constraint_repr", 1))))
    except (TypeError, ValueError):
        params_dict["EXTRA_CONSTRAINT_REPRESENTATIVENESS"] = 1
    params_dict["MIN_VARS_PER_CONSTRAINT"] = int(form.get("vars_per_ctc_min", 1))
    max_feats = int(params_dict.get("MAX_FEATURES", 10000))
    params_dict["MAX_VARS_PER_CONSTRAINT"] = min(int(form.get("vars_per_ctc_max", 1)), max_feats)

    # Boolean level
    params_dict["PROB_NOT"] = _safe_float(form.get("prob_not"), 0.3)
    params_dict["PROB_AND"] = _safe_float(form.get("prob_and"), 0.7)
    params_dict["PROB_OR_CT"] = _safe_float(form.get("prob_or"), 0.1)
    params_dict["PROB_IMPLICATION"] = _safe_float(form.get("prob_implies"), 0.1)
    params_dict["PROB_EQUIVALENCE"] = _safe_float(form.get("prob_equiv"), 0.1)
    # Renormalise boolean connectives to exact 1.0
    bkeys = ["PROB_AND", "PROB_OR_CT", "PROB_IMPLICATION", "PROB_EQUIVALENCE"]
    btot = sum(params_dict[k] for k in bkeys)
    if btot > 0:
        for k in bkeys:
            params_dict[k] = round(params_dict[k] / btot, 6)
        params_dict[bkeys[-1]] += round(1.0 - sum(params_dict[k] for k in bkeys), 6)

    arith_on = bool(params_dict.get("ARITHMETIC_LEVEL", False))
    agg_on = bool(params_dict.get("AGGREGATE_FUNCTIONS", False))
    if arith_on:
        params_dict["PROB_SUM"] = _safe_float(form.get("prob_plus"), 0.7)
        params_dict["PROB_SUBSTRACT"] = _safe_float(form.get("prob_minus"), 0.2)
        params_dict["PROB_MULTIPLY"] = _safe_float(form.get("prob_times"), 0.1)
        params_dict["PROB_DIVIDE"] = _safe_float(form.get("prob_div"), 0.0)
        if agg_on:
            params_dict["PROB_SUM_FUNCTION"] = _safe_float(form.get("prob_sum"), 0.0)
            params_dict["PROB_AVG_FUNCTION"] = _safe_float(form.get("prob_avg"), 0.0)
        else:
            params_dict["PROB_SUM_FUNCTION"] = 0.0
            params_dict["PROB_AVG_FUNCTION"] = 0.0
        params_dict["PROB_EQUALS"] = _safe_float(form.get("prob_eq"), 0.1)
        params_dict["PROB_LESS"] = _safe_float(form.get("prob_lt"), 0.2)
        params_dict["PROB_GREATER"] = _safe_float(form.get("prob_gt"), 0.7)
        params_dict["PROB_LESS_EQUALS"] = _safe_float(form.get("prob_leq"), 0.0)
        params_dict["PROB_GREATER_EQUALS"] = _safe_float(form.get("prob_geq"), 0.0)
    else:
        for k in (
            "PROB_SUM",
            "PROB_SUBSTRACT",
            "PROB_MULTIPLY",
            "PROB_DIVIDE",
            "PROB_SUM_FUNCTION",
            "PROB_AVG_FUNCTION",
            "PROB_EQUALS",
            "PROB_LESS",
            "PROB_GREATER",
            "PROB_LESS_EQUALS",
            "PROB_GREATER_EQUALS",
        ):
            params_dict[k] = 0.0

    type_on = bool(params_dict.get("TYPE_LEVEL", False))
    str_on = bool(params_dict.get("STRING_CONSTRAINTS", False))
    if type_on and str_on:
        params_dict["PROB_LEN_FUNCTION"] = _safe_float(form.get("prob_len"), 0.7)
    else:
        params_dict["PROB_LEN_FUNCTION"] = 0.0

    # CTC type distribution
    params_dict["CTC_DIST_BOOLEAN"] = _safe_float(form.get("ctc_dist_boolean"), 0.7 if arith_on or type_on else 1.0)
    params_dict["CTC_DIST_INTEGER"] = _safe_float(form.get("ctc_dist_integer"), 0.2) if arith_on else 0.0
    params_dict["CTC_DIST_REAL"] = _safe_float(form.get("ctc_dist_real"), 0.1) if arith_on else 0.0
    params_dict["CTC_DIST_STRING"] = _safe_float(form.get("ctc_dist_string"), 0.0) if type_on and str_on else 0.0
    cks = ["CTC_DIST_BOOLEAN", "CTC_DIST_INTEGER", "CTC_DIST_REAL", "CTC_DIST_STRING"]
    ctot = sum(params_dict[k] for k in cks)
    if ctot > 0:
        for k in cks:
            params_dict[k] = round(params_dict[k] / ctot, 6)
        params_dict[cks[0]] += round(1.0 - sum(params_dict[k] for k in cks), 6)
    else:
        params_dict["CTC_DIST_BOOLEAN"] = 1.0


def _apply_step5_attributes(params_dict, form):
    """Persist attribute settings from step 5."""
    random_attributes = "random_attributes" in form
    params_dict["RANDOM_ATTRIBUTES"] = random_attributes
    if random_attributes:
        params_dict["MIN_ATTRIBUTES"] = int(form.get("min_attributes", 1))
        params_dict["MAX_ATTRIBUTES"] = int(form.get("max_attributes", 5))
        params_dict["ATTRIBUTES_LIST"] = []
        params_dict["ATTRIBUTE_ATTACH_PROBS"] = []
        params_dict["ATTRIBUTE_IN_CONSTRAINTS"] = []
        arith_on = bool(params_dict.get("ARITHMETIC_LEVEL", False))
        type_on = bool(params_dict.get("TYPE_LEVEL", False))
        dist = {
            "ATTR_DIST_BOOLEAN": _safe_float(form.get("dist_boolean_atr"), 0.7),
            "ATTR_DIST_INTEGER": _safe_float(form.get("dist_integer_atr"), 0.0) if arith_on else 0.0,
            "ATTR_DIST_REAL": _safe_float(form.get("dist_real_atr"), 0.0) if arith_on else 0.0,
            "ATTR_DIST_STRING": _safe_float(form.get("dist_string_atr"), 0.0) if type_on else 0.0,
        }
        dtot = sum(dist.values())
        if dtot > 0:
            for k in dist:
                dist[k] = round(dist[k] / dtot, 6)
            residue = round(1.0 - sum(dist.values()), 6)
            dominant = max(dist, key=dist.get)
            dist[dominant] = round(dist[dominant] + residue, 6)
        params_dict.update(dist)
    else:
        attrs, probs, in_ctc = _collect_manual_attributes(form, params_dict)
        params_dict["MIN_ATTRIBUTES"] = None
        params_dict["MAX_ATTRIBUTES"] = None
        params_dict["ATTRIBUTES_LIST"] = attrs
        params_dict["ATTRIBUTE_ATTACH_PROBS"] = probs
        params_dict["ATTRIBUTE_IN_CONSTRAINTS"] = in_ctc


def _apply_step6_output(params_dict, form):
    """Persist output options from step 6."""
    params_dict["ENSURE_SATISFIABLE"] = "ensure_satisfiable" in form
    params_dict["INCLUDE_FEATURE_COUNT_SUFFIX"] = "feature_count_suffix" in form
    params_dict["INCLUDE_CONSTRAINT_COUNT_SUFFIX"] = "constraint_count_suffix" in form


def add_level_flags(values: dict, params_dict: dict) -> dict:
    values.update(
        {
            "arithmetic_level": params_dict.get("ARITHMETIC_LEVEL", False),
            "type_level": params_dict.get("TYPE_LEVEL", False),
            "feature_cardinality": params_dict.get("FEATURE_CARDINALITY", False),
            "aggregate_functions": params_dict.get("AGGREGATE_FUNCTIONS", False),
            "string_constraints": params_dict.get("STRING_CONSTRAINTS", False),
            "group_cardinality": params_dict.get("GROUP_CARDINALITY", False),
        }
    )
    return values


# ─── Generic helpers ─────────────────────────────────────────────────────


def _safe_float(value, default=0.0):
    """Parse a form value as float, tolerating the Spanish-locale decimal
    comma some browsers submit for <input type="number">. The default is
    always coerced to float so callers can't accidentally propagate a
    string through arithmetic."""
    try:
        fallback = float(default)
    except (TypeError, ValueError):
        fallback = 0.0
    if value is None:
        return fallback
    text = str(value).strip().replace(",", ".")
    if text == "":
        return fallback
    try:
        return float(text)
    except ValueError:
        return fallback


def save_step_state(step: int, form, checkbox_fields=None):
    """Cache raw form values so we can repaint the page if validation fails."""
    checkbox_fields = checkbox_fields or []
    wizard = session.get("wizard", {})
    data = dict(form)
    for cb in checkbox_fields:
        data[cb] = cb in form
    wizard[str(step)] = data
    session["wizard"] = wizard


def load_step_state(step: int, defaults: dict):
    wizard = session.get("wizard", {})
    saved = wizard.get(str(step), {})
    out = defaults.copy()
    out.update(saved)
    return out


DRAFT_PERSISTERS = {
    2: _apply_step2_levels,
    3: _apply_step3_tree,
    4: _apply_step4_constraints,
    5: _apply_step5_attributes,
    6: _apply_step6_output,
}


def update_summary_draft(step: int, form) -> dict:
    params_dict = session.get("params", {}) or {}

    if step == 1:
        try:
            nm = form.get("num_models_val")
            if nm:
                params_dict["NUM_MODELS"] = max(1, min(1000, int(nm)))
        except (TypeError, ValueError):
            pass

        try:
            sd = form.get("seed")
            if sd:
                params_dict["SEED"] = max(1, int(sd))
        except (TypeError, ValueError):
            pass

        if form.get("name_prefix") is not None:
            params_dict["NAME_PREFIX"] = form.get("name_prefix", "")

    elif step in DRAFT_PERSISTERS:
        try:
            DRAFT_PERSISTERS[step](params_dict, form)
        except Exception:
            pass

    session["params"] = params_dict
    return params_dict


# ─── Main Service class ─────────────────────────────────────────────────────


class GeneratorWizardService:
    @staticmethod
    def reset_wizard_state() -> None:
        session.pop("params", None)
        session.pop("wizard", None)

    @staticmethod
    def _redirect(endpoint: str) -> WizardRouteResult:
        return WizardRouteResult(redirect_endpoint=endpoint)

    @staticmethod
    def _render_step(step: int, values, errors=None, extra_context=None) -> WizardRouteResult:
        context = {
            "current_step": step,
            "errors": errors or {},
            "values": values,
        }

        if extra_context:
            context.update(extra_context)

        return WizardRouteResult(
            template=f"generator/step{step}.html",
            context=context,
        )

    @staticmethod
    def _step5_flags(params_dict: dict) -> dict:
        return {
            "arithmetic_level": params_dict.get("ARITHMETIC_LEVEL", False),
            "type_level": params_dict.get("TYPE_LEVEL", False),
            "string_constraints": params_dict.get("STRING_CONSTRAINTS", False),
        }

    @staticmethod
    def get_step1() -> WizardRouteResult:
        values = build_step1_values(session.get("params", {}))
        return GeneratorWizardService._render_step(1, values)

    @staticmethod
    def post_step1(form) -> WizardRouteResult:
        errors, values = validate_step1_form(form)

        if errors:
            return GeneratorWizardService._render_step(1, values, errors)

        params_dict = session.get("params", {}) or {}

        try:
            _apply_step1_batch(params_dict, form)
        except (TypeError, ValueError) as exc:
            errors["global"] = str(exc)
            return GeneratorWizardService._render_step(1, form, errors)

        session["params"] = params_dict

        return GeneratorWizardService._redirect("generator.step2")

    @staticmethod
    def get_step2() -> WizardRouteResult:
        values = build_step2_values(session.get("params", {}))
        return GeneratorWizardService._render_step(2, values)

    @staticmethod
    def post_step2(form) -> WizardRouteResult:
        nav = form.get("nav", "next")

        save_step_state(2, form, checkbox_fields=step2_checkbox_fields)

        params_dict = session.get("params", {}) or {}
        _apply_step2_levels(params_dict, form)
        session["params"] = params_dict

        if nav == "prev":
            return GeneratorWizardService._redirect("generator.step1")

        errors, values = validate_step2_form(form)

        if errors:
            return GeneratorWizardService._render_step(2, values, errors)

        return GeneratorWizardService._redirect("generator.step3")

    @staticmethod
    def get_step3() -> WizardRouteResult:
        params_dict = session.get("params")

        if not params_dict:
            return GeneratorWizardService._redirect("generator.landing")

        values = build_step3_values(params_dict)
        return GeneratorWizardService._render_step(3, values)

    @staticmethod
    def post_step3(form) -> WizardRouteResult:
        params_dict = session.get("params")

        if not params_dict:
            return GeneratorWizardService._redirect("generator.landing")

        nav = form.get("nav", "next")
        save_step_state(3, form, checkbox_fields=[])

        if nav == "prev":
            _apply_step3_tree(params_dict, form)
            session["params"] = params_dict
            return GeneratorWizardService._redirect("generator.step2")

        errors, values = validate_step3_form(form, params_dict)
        add_level_flags(values, params_dict)

        if errors:
            return GeneratorWizardService._render_step(3, values, errors)

        _apply_step3_tree(params_dict, form)
        session["params"] = params_dict

        return GeneratorWizardService._redirect("generator.step4")

    @staticmethod
    def get_step4() -> WizardRouteResult:
        params_dict = session.get("params")

        if not params_dict:
            return GeneratorWizardService._redirect("generator.landing")

        values = build_step4_values(params_dict)
        return GeneratorWizardService._render_step(4, values)

    @staticmethod
    def post_step4(form) -> WizardRouteResult:
        params_dict = session.get("params")

        if not params_dict:
            return GeneratorWizardService._redirect("generator.landing")

        nav = form.get("nav", "next")
        save_step_state(4, form, checkbox_fields=[])

        if nav == "prev":
            _apply_step4_constraints(params_dict, form)
            session["params"] = params_dict
            return GeneratorWizardService._redirect("generator.step3")

        max_features = int(params_dict.get("MAX_FEATURES", 10000))
        errors, values = validate_step4_form(form, max_features, params_dict)
        add_level_flags(values, params_dict)

        if errors:
            return GeneratorWizardService._render_step(4, values, errors)

        _apply_step4_constraints(params_dict, form)
        session["params"] = params_dict

        return GeneratorWizardService._redirect("generator.step5")

    @staticmethod
    def get_step5() -> WizardRouteResult:
        params_dict = session.get("params")

        if not params_dict:
            return GeneratorWizardService._redirect("generator.landing")

        values = build_step5_values(params_dict)

        return GeneratorWizardService._render_step(
            5,
            values,
            extra_context=GeneratorWizardService._step5_flags(params_dict),
        )

    @staticmethod
    def post_step5(form) -> WizardRouteResult:
        params_dict = session.get("params")

        if not params_dict:
            return GeneratorWizardService._redirect("generator.landing")

        nav = form.get("nav", "next")
        save_step_state(5, form, checkbox_fields=step5_checkbox_fields)

        if nav == "prev":
            _apply_step5_attributes(params_dict, form)
            session["params"] = params_dict
            return GeneratorWizardService._redirect("generator.step4")

        errors, values = validate_step5_form(form, params_dict)

        if errors:
            return GeneratorWizardService._render_step(
                5,
                values,
                errors,
                extra_context=GeneratorWizardService._step5_flags(params_dict),
            )

        _apply_step5_attributes(params_dict, form)
        session["params"] = params_dict

        return GeneratorWizardService._redirect("generator.step6")

    @staticmethod
    def get_step6() -> WizardRouteResult:
        params_dict = session.get("params")

        if not params_dict:
            return GeneratorWizardService._redirect("generator.landing")

        values = build_step6_values(params_dict)
        return GeneratorWizardService._render_step(6, values)

    @staticmethod
    def post_step6(form) -> WizardRouteResult:
        params_dict = session.get("params")

        if not params_dict:
            return GeneratorWizardService._redirect("generator.landing")

        nav = form.get("nav", "next")

        save_step_state(6, form, checkbox_fields=step6_checkbox_fields)
        _apply_step6_output(params_dict, form)
        session["params"] = params_dict

        if nav == "prev":
            return GeneratorWizardService._redirect("generator.step5")

        return GeneratorWizardService._redirect("generator.step6")

    @staticmethod
    def get_params_json() -> tuple[dict, int]:
        params_dict = session.get("params")

        if not params_dict:
            return {"error": "Generator parameters missing"}, 400

        return params_dict, 200

    @staticmethod
    def refresh_summary(step: int, form) -> dict:
        return update_summary_draft(step, form)

    @staticmethod
    def serialize_generated_model(
        fm: FeatureModel,
        model: FmgeneratorModel,
        index: int,
    ):
        content = UVLWriter(None, fm).transform()

        feature_count = len(list(fm.get_features()))
        constraint_count = len(getattr(fm, "ctcs", []))

        base_name = model.naming.name_prefix.strip() if model.naming.name_prefix else "fm"

        if model.naming.include_feature_count_suffix and model.naming.include_constraint_count_suffix:
            filename = f"{base_name}_{feature_count}f_{constraint_count}c.uvl"

        elif model.naming.include_feature_count_suffix:
            filename = f"{base_name}_{feature_count}f.uvl"

        elif model.naming.include_constraint_count_suffix:
            filename = f"{base_name}_{constraint_count}c.uvl"

        elif model.num_models > 1:
            filename = f"{base_name}_{index}.uvl"

        else:
            filename = f"{base_name}.uvl"

        return {
            "filename": filename,
            "content": content,
            "features": feature_count,
            "constraints": constraint_count,
        }

    @staticmethod
    def generate_sat_models(params_dict):
        logger.warning("BACKEND SAT GENERATION ACTIVATED")
        sat_params = dict(params_dict)
        sat_params["ENSURE_SATISFIABLE"] = True
        model = FmgeneratorModel.from_flat_dict(sat_params)
        results = []

        for index in range(model.num_models):
            fm = None
            attempt = 0

            while attempt < SAT_MAX_ATTEMPTS:
                logger.warning(f"Model {index}, attempt {attempt}")
                operation = GenerateFeatureModel()
                operation.execute(
                    model=model,
                    index=index,
                    attempt=attempt,
                )
                candidate = operation.get_result()

                if GeneratorWizardService.is_satisfiable(candidate):
                    fm = candidate
                    break

                attempt += 1

            if fm is None:
                raise SatisfiableModelGenerationError(
                    model_number=index + 1,
                    attempts=SAT_MAX_ATTEMPTS,
                )

            results.append(
                GeneratorWizardService.serialize_generated_model(
                    fm,
                    model,
                    index,
                )
            )

        return results

    @staticmethod
    def is_satisfiable(feature_model):
        """
        Checks satisfiability by translating the generated feature model
        into a PySAT model and executing FlamaPy SAT operation.
        """
        logger.warning("Checking SAT...")

        pysat_model = FmToPysat(feature_model).transform()

        operation = PySATSatisfiable()
        operation.execute(pysat_model)

        result = operation.get_result()

        logger.warning(f"SAT result: {result}")

        return result
