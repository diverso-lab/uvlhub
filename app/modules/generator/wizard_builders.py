from flask import session

from app.modules.generator.constants import STEP4_UI_DEFAULTS
from app.modules.generator.wizard_state import load_step_state


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
        defaults.update({
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
        })
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
        "dist_boolean": params_dict.get("DIST_BOOLEAN", 0.7),
        "dist_integer": params_dict.get("DIST_INTEGER", 0.1),
        "dist_real": params_dict.get("DIST_REAL", 0.1),
        "dist_string": params_dict.get("DIST_STRING", 0.1),
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