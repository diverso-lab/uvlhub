import pytest
from werkzeug.datastructures import MultiDict

from app.features.generator.wizard import (
    _apply_step1_batch,
    _apply_step2_levels,
    _apply_step3_tree,
    _apply_step4_constraints,
    _apply_step5_attributes,
    _apply_step6_output,
    _collect_manual_attributes,
    _safe_float,
    add_level_flags,
)

pytestmark = pytest.mark.integration


def test_apply_step2_type_enables_arithmetic():
    params = {}
    form = MultiDict({"type_level": "on"})

    _apply_step2_levels(params, form)

    assert params["BOOLEAN_LEVEL"] is True
    assert params["TYPE_LEVEL"] is True
    assert params["ARITHMETIC_LEVEL"] is True


def test_apply_step3_normalizes_relation_distribution():
    params = {"GROUP_CARDINALITY": False, "FEATURE_CARDINALITY": False}
    form = MultiDict(
        {
            "num_features_min": "10",
            "num_features_max": "20",
            "max_tree_depth": "5",
            "dist_optional": "2",
            "dist_mandatory": "2",
            "dist_alternative": "2",
            "dist_or": "2",
        }
    )

    _apply_step3_tree(params, form)

    total = (
        params["DIST_OPTIONAL"]
        + params["DIST_MANDATORY"]
        + params["DIST_ALTERNATIVE"]
        + params["DIST_OR"]
        + params["DIST_GROUP_CARDINALITY"]
    )
    assert total == 1.0


def test_apply_step4_disables_arithmetic_probs_when_arithmetic_off():
    params = {
        "ARITHMETIC_LEVEL": False,
        "TYPE_LEVEL": False,
        "STRING_CONSTRAINTS": False,
        "MAX_FEATURES": 20,
    }
    form = MultiDict(
        {
            "num_constraints_min": "1",
            "num_constraints_max": "5",
            "extra_constraint_repr": "1",
            "vars_per_ctc_min": "1",
            "vars_per_ctc_max": "5",
            "prob_not": "0.3",
            "prob_and": "1",
            "prob_or": "0",
            "prob_implies": "0",
            "prob_equiv": "0",
            "ctc_dist_boolean": "1",
        }
    )

    _apply_step4_constraints(params, form)

    assert params["PROB_SUM"] == 0.0
    assert params["PROB_EQUALS"] == 0.0
    assert params["CTC_DIST_BOOLEAN"] == 1.0
    assert params["CTC_DIST_INTEGER"] == 0.0


def test_apply_step5_random_attrs_normalizes_distribution():
    params = {"ARITHMETIC_LEVEL": True, "TYPE_LEVEL": True}
    form = MultiDict(
        {
            "random_attributes": "on",
            "min_attributes": "1",
            "max_attributes": "4",
            "dist_boolean_atr": "1",
            "dist_integer_atr": "1",
            "dist_real_atr": "1",
            "dist_string_atr": "1",
        }
    )

    _apply_step5_attributes(params, form)

    total = (
        params["ATTR_DIST_BOOLEAN"]
        + params["ATTR_DIST_INTEGER"]
        + params["ATTR_DIST_REAL"]
        + params["ATTR_DIST_STRING"]
    )

    assert total == 1.0


def test_apply_step3_normalizes_relation_distribution_with_group_cardinality():
    params = {"GROUP_CARDINALITY": True, "FEATURE_CARDINALITY": False}
    form = MultiDict(
        {
            "num_features_min": "10",
            "num_features_max": "20",
            "max_tree_depth": "5",
            "dist_optional": "1",
            "dist_mandatory": "1",
            "dist_alternative": "1",
            "dist_or": "1",
            "dist_group_cardinality": "1",
            "group_cardinality_min": "1",
            "group_cardinality_max": "4",
        }
    )

    _apply_step3_tree(params, form)

    total = (
        params["DIST_OPTIONAL"]
        + params["DIST_MANDATORY"]
        + params["DIST_ALTERNATIVE"]
        + params["DIST_OR"]
        + params["DIST_GROUP_CARDINALITY"]
    )

    assert total == 1.0
    assert params["DIST_GROUP_CARDINALITY"] > 0.0
    assert params["GROUP_CARDINALITY_MIN"] == 1
    assert params["GROUP_CARDINALITY_MAX"] == 4


def test_apply_step5_masks_unavailable_attribute_types_when_levels_are_off():
    params = {"ARITHMETIC_LEVEL": False, "TYPE_LEVEL": False}
    form = MultiDict(
        {
            "random_attributes": "on",
            "min_attributes": "1",
            "max_attributes": "4",
            "dist_boolean": "1",
            "dist_integer": "1",
            "dist_real": "1",
            "dist_string": "1",
        }
    )

    _apply_step5_attributes(params, form)

    assert params["ATTR_DIST_BOOLEAN"] == 1.0
    assert params["ATTR_DIST_INTEGER"] == 0.0
    assert params["ATTR_DIST_REAL"] == 0.0
    assert params["ATTR_DIST_STRING"] == 0.0


def test_safe_float_accepts_comma_and_invalid_values_fall_back():
    assert _safe_float("1,25") == 1.25
    assert _safe_float("not-a-number", "also-invalid") == 0.0


def test_apply_step1_persists_batch_fields():
    params = {}

    _apply_step1_batch(
        params,
        MultiDict(
            {
                "num_models_val": "3",
                "seed": "42",
                "name_prefix": "demo",
            }
        ),
    )

    assert params == {
        "NUM_MODELS": 3,
        "SEED": 42,
        "NAME_PREFIX": "demo",
    }


def test_add_level_flags_copies_all_level_values():
    values = {"preserved": "value"}
    params = {
        "ARITHMETIC_LEVEL": True,
        "TYPE_LEVEL": True,
        "FEATURE_CARDINALITY": True,
        "AGGREGATE_FUNCTIONS": False,
        "STRING_CONSTRAINTS": True,
        "GROUP_CARDINALITY": False,
    }

    result = add_level_flags(values, params)

    assert result is values
    assert values == {
        "preserved": "value",
        "arithmetic_level": True,
        "type_level": True,
        "feature_cardinality": True,
        "aggregate_functions": False,
        "string_constraints": True,
        "group_cardinality": False,
    }


def test_collect_manual_attributes_keeps_supported_types_only():
    form = MultiDict(
        {
            "attr_name_0": "enabled",
            "attr_type_0": "boolean",
            "attr_attach_prob_0": "0.25",
            "attr_use_in_constraints_0": "on",
            "attr_value_true_0": "on",
            "attr_value_false_0": "on",
            "attr_name_1": "count",
            "attr_type_1": "integer",
            "attr_attach_prob_1": "0,5",
            "attr_use_in_constraints_1": "on",
            "attr_min_value_1": "1",
            "attr_max_value_1": "4",
            "attr_name_2": "label",
            "attr_type_2": "string",
            "attr_attach_prob_2": "1",
            "attr_use_in_constraints_2": "on",
            "attr_min_value_2": "0",
            "attr_max_value_2": "8",
            "attr_name_3": "ignored",
            "attr_type_3": "unknown",
            "attr_attach_prob_3": "1",
        }
    )
    params = {
        "ARITHMETIC_LEVEL": True,
        "TYPE_LEVEL": True,
        "STRING_CONSTRAINTS": True,
    }

    attributes, probabilities, use_in_constraints = _collect_manual_attributes(form, params)

    assert [attribute["type"] for attribute in attributes] == [
        "Boolean",
        "Integer",
        "String",
    ]
    assert attributes[0]["value"] == [True, False]
    assert attributes[1]["use_in_constraints"] is True
    assert attributes[2]["use_in_constraints"] is True
    assert probabilities == [0.25, 0.5, 1.0]
    assert use_in_constraints == [True, True, True]


def test_apply_step4_falls_back_when_extra_repr_and_ctc_dist_are_invalid():
    params = {
        "ARITHMETIC_LEVEL": False,
        "TYPE_LEVEL": False,
        "STRING_CONSTRAINTS": False,
        "MAX_FEATURES": 4,
    }
    form = MultiDict(
        {
            "num_constraints_min": "1",
            "num_constraints_max": "2",
            "extra_constraint_repr": "invalid",
            "vars_per_ctc_min": "1",
            "vars_per_ctc_max": "2",
            "prob_not": "0",
            "prob_and": "0",
            "prob_or": "0",
            "prob_implies": "0",
            "prob_equiv": "0",
            "ctc_dist_boolean": "0",
        }
    )

    _apply_step4_constraints(params, form)

    assert params["EXTRA_CONSTRAINT_REPRESENTATIVENESS"] == 1
    assert params["CTC_DIST_BOOLEAN"] == 1.0


def test_apply_step6_output_persists_checkboxes():
    params = {}

    _apply_step6_output(
        params,
        MultiDict(
            {
                "ensure_satisfiable": "on",
                "constraint_count_suffix": "on",
            }
        ),
    )

    assert params == {
        "ENSURE_SATISFIABLE": True,
        "INCLUDE_FEATURE_COUNT_SUFFIX": False,
        "INCLUDE_CONSTRAINT_COUNT_SUFFIX": True,
    }
