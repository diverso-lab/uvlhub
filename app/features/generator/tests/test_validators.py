"""Unit tests for the per-step form validators.

The validators are pure functions (no DB, no request context) so we drive
each branch with parametrised inputs here. Covers every knob in every
step, both happy and sad paths.
"""

import pytest
from werkzeug.datastructures import MultiDict

import app.features.generator.wizard as wizard
from app.features.generator.wizard import (
    validate_step1_form,
    validate_step2_form,
    validate_step3_form,
    validate_step4_form,
    validate_step5_form,
    validate_step6_form,
)

pytestmark = pytest.mark.unit


def _step3_form(**overrides):
    data = {
        "num_features_min": "5",
        "num_features_max": "20",
        "max_tree_depth": "5",
        "dist_optional": "0.3",
        "dist_mandatory": "0.3",
        "dist_alternative": "0.2",
        "dist_or": "0.2",
        "prob_fc": "0.1",
        "group_cardinality_min": "1",
        "group_cardinality_max": "6",
        "dist_group_cardinality": "0.0",
    }
    data.update(overrides)
    return MultiDict(data)


def _step4_form(**overrides):
    data = {
        "num_constraints_min": "1",
        "num_constraints_max": "5",
        "extra_constraint_repr": "1",
        "vars_per_ctc_min": "1",
        "vars_per_ctc_max": "5",
        "prob_not": "0.3",
        "prob_and": "0.4",
        "prob_or": "0.2",
        "prob_implies": "0.2",
        "prob_equiv": "0.2",
        "prob_plus": "0.25",
        "prob_minus": "0.25",
        "prob_times": "0.25",
        "prob_div": "0.25",
        "prob_sum": "0.0",
        "prob_avg": "0.0",
        "prob_eq": "0.2",
        "prob_lt": "0.2",
        "prob_gt": "0.2",
        "prob_leq": "0.2",
        "prob_geq": "0.2",
        "prob_len": "0.5",
        "ctc_dist_boolean": "1.0",
        "ctc_dist_integer": "0.0",
        "ctc_dist_real": "0.0",
        "ctc_dist_string": "0.0",
    }
    data.update(overrides)
    return MultiDict(data)


@pytest.mark.parametrize(
    ("data", "field"),
    [
        ({"num_models_val": "invalid", "seed": "1"}, "num_models_val"),
        ({"num_models_val": "1", "seed": "invalid"}, "seed"),
    ],
)
def test_step1_rejects_non_numeric_values(data, field):
    errors, _ = validate_step1_form(MultiDict(data))

    assert field in errors


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"num_features_min": "0"}, "num_features_min"),
        ({"num_features_max": "0"}, "num_features_max"),
        ({"num_features_min": "20", "num_features_max": "5"}, "num_features_max"),
        ({"max_tree_depth": "invalid"}, "max_tree_depth"),
        ({"max_tree_depth": "30"}, "max_tree_depth"),
        ({"dist_optional": "2"}, "dist_optional"),
    ],
)
def test_step3_rejects_additional_invalid_values(overrides, field):
    errors, _ = validate_step3_form(_step3_form(**overrides))

    assert field in errors


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"group_cardinality_min": "0"}, "group_cardinality_min"),
        ({"group_cardinality_max": "0"}, "group_cardinality_max"),
        ({"group_cardinality_max": "21"}, "group_cardinality_max"),
        ({"group_cardinality_min": "5", "group_cardinality_max": "2"}, "group_cardinality_max"),
        ({"group_cardinality_min": "invalid"}, "group_cardinality_min"),
        ({"group_cardinality_max": "invalid"}, "group_cardinality_max"),
    ],
)
def test_step3_rejects_invalid_group_cardinality_values(overrides, field):
    errors, _ = validate_step3_form(
        _step3_form(**overrides),
        {"GROUP_CARDINALITY": True},
    )

    assert field in errors


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"num_constraints_min": "0"}, "num_constraints_min"),
        ({"num_constraints_max": "0"}, "num_constraints_max"),
        ({"num_constraints_min": "5", "num_constraints_max": "1"}, "num_constraints_max"),
        ({"extra_constraint_repr": "invalid"}, "extra_constraint_repr"),
        ({"vars_per_ctc_max": "0"}, "vars_per_ctc_max"),
        ({"extra_constraint_repr": "0"}, "extra_constraint_repr"),
        ({"extra_constraint_repr": "10"}, "extra_constraint_repr"),
        ({"vars_per_ctc_min": "0"}, "vars_per_ctc_min"),
        ({"vars_per_ctc_max": "10"}, "vars_per_ctc_max"),
        ({"vars_per_ctc_min": "5", "vars_per_ctc_max": "2"}, "vars_per_ctc_max"),
        ({"prob_not": "2"}, "prob_not"),
    ],
)
def test_step4_rejects_additional_invalid_values(overrides, field):
    errors, _ = validate_step4_form(
        _step4_form(**overrides),
        max_features=5,
    )

    assert field in errors


def test_step4_rejects_invalid_arithmetic_and_comparison_distributions():
    errors, _ = validate_step4_form(
        _step4_form(
            prob_plus="0",
            prob_minus="0",
            prob_times="0",
            prob_div="0",
            prob_eq="0",
            prob_lt="0",
            prob_gt="0",
            prob_leq="0",
            prob_geq="0",
        ),
        params_dict={"ARITHMETIC_LEVEL": True},
    )

    assert "arithmetic_sum" in errors
    assert "cmp_sum" in errors


def test_step4_rejects_invalid_string_probability():
    errors, _ = validate_step4_form(
        _step4_form(prob_len="2"),
        params_dict={
            "TYPE_LEVEL": True,
            "STRING_CONSTRAINTS": True,
        },
    )

    assert "prob_len" in errors


def test_step4_rejects_invalid_constraint_type_distribution():
    errors, _ = validate_step4_form(
        _step4_form(
            ctc_dist_boolean="0",
            ctc_dist_integer="2",
        ),
        params_dict={"ARITHMETIC_LEVEL": True},
    )

    assert "ctc_dist_integer" in errors
    assert "ctc_dist_sum" in errors


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"min_attributes": "-1"}, "min_attributes"),
        ({"max_attributes": "0"}, "max_attributes"),
        ({"min_attributes": "5", "max_attributes": "1"}, "max_attributes"),
        ({"min_attributes": "invalid"}, "min_attributes"),
        ({"max_attributes": "invalid"}, "max_attributes"),
        ({"dist_boolean_atr": "2"}, "dist_boolean_atr"),
    ],
)
def test_step5_rejects_additional_random_attribute_values(overrides, field):
    form = {
        "random_attributes": "on",
        "min_attributes": "1",
        "max_attributes": "4",
        "dist_boolean_atr": "1",
        "dist_integer_atr": "0",
        "dist_real_atr": "0",
        "dist_string_atr": "0",
    }
    form.update(overrides)

    errors, _ = validate_step5_form(MultiDict(form))

    assert field in errors


def test_step5_rejects_manual_boolean_without_values():
    errors, _ = validate_step5_form(
        MultiDict(
            {
                "attr_name_0": "enabled",
                "attr_type_0": "boolean",
                "attr_attach_prob_0": "0.5",
            }
        )
    )

    assert "attr_value_bool_0" in errors


def test_step5_rejects_manual_integer_without_arithmetic():
    errors, _ = validate_step5_form(
        MultiDict(
            {
                "attr_name_0": "quantity",
                "attr_type_0": "integer",
                "attr_use_in_constraints_0": "on",
                "attr_attach_prob_0": "0.5",
                "attr_min_value_0": "1",
                "attr_max_value_0": "5",
            }
        ),
        {"ARITHMETIC_LEVEL": False},
    )

    assert "attr_use_in_constraints_0" in errors


def test_step5_rejects_manual_string_without_string_constraints():
    errors, _ = validate_step5_form(
        MultiDict(
            {
                "attr_name_0": "description",
                "attr_type_0": "string",
                "attr_use_in_constraints_0": "on",
                "attr_attach_prob_0": "2",
                "attr_min_value_0": "-1",
                "attr_max_value_0": "3",
            }
        ),
        {
            "TYPE_LEVEL": False,
            "STRING_CONSTRAINTS": False,
        },
    )

    assert "attr_use_in_constraints_0" in errors
    assert "attr_attach_prob_0" in errors
    assert "attr_minmax_0" in errors


def test_step5_rejects_manual_real_with_invalid_range():
    errors, _ = validate_step5_form(
        MultiDict(
            {
                "attr_name_0": "price",
                "attr_type_0": "real",
                "attr_attach_prob_0": "0.5",
                "attr_min_value_0": "5.5",
                "attr_max_value_0": "1.5",
            }
        )
    )

    assert "attr_minmax_0" in errors


def test_step5_rejects_manual_attribute_with_non_numeric_range():
    errors, _ = validate_step5_form(
        MultiDict(
            {
                "attr_name_0": "quantity",
                "attr_type_0": "integer",
                "attr_attach_prob_0": "0.5",
                "attr_min_value_0": "invalid",
                "attr_max_value_0": "invalid",
            }
        )
    )

    assert "attr_minmax_0" in errors


def test_step6_accepts_all_output_options():
    errors, values = validate_step6_form(
        MultiDict(
            {
                "ensure_satisfiable": "on",
                "feature_count_suffix": "on",
                "constraint_count_suffix": "on",
            }
        )
    )

    assert errors == {}
    assert values == {
        "ensure_satisfiable": True,
        "feature_count_suffix": True,
        "constraint_count_suffix": True,
    }


def test_step1_rejects_batch_size_that_could_break_generation():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "1001", "seed": "42"}))

    assert "num_models_val" in errors


def test_step2_rejects_minor_levels_without_required_major_levels():
    errors, _ = validate_step2_form(
        MultiDict(
            {
                "feature_cardinality": "on",
                "aggregate_functions": "on",
                "string_constraints": "on",
            }
        )
    )

    assert "feature_cardinality" in errors
    assert "aggregate_functions" in errors
    assert "string_constraints" in errors


def _valid_step3(**overrides):
    data = {
        "num_features_min": "10",
        "num_features_max": "50",
        "max_tree_depth": "5",
        "dist_optional": "0.3",
        "dist_mandatory": "0.3",
        "dist_alternative": "0.2",
        "dist_or": "0.2",
    }
    data.update(overrides)
    return MultiDict(data)


def test_step3_rejects_invalid_relation_distribution():
    errors, _ = validate_step3_form(
        _valid_step3(
            dist_optional="0.9",
            dist_mandatory="0.9",
            dist_alternative="0",
            dist_or="0",
        )
    )

    assert "rel_dist_total" in errors


def test_step3_rejects_group_cardinality_distribution_without_group_weight():
    errors, _ = validate_step3_form(
        _valid_step3(
            dist_optional="0.2",
            dist_mandatory="0.2",
            dist_alternative="0.2",
            dist_or="0.2",
        ),
        params_dict={"GROUP_CARDINALITY": True},
    )

    assert "rel_dist_total" in errors


def test_step3_rejects_invalid_feature_cardinality_probability():
    errors, _ = validate_step3_form(
        _valid_step3(prob_fc="1.5"),
        params_dict={"FEATURE_CARDINALITY": True},
    )

    assert "prob_fc" in errors


def _valid_step4(**overrides):
    data = {
        "num_constraints_min": "1",
        "num_constraints_max": "5",
        "extra_constraint_repr": "1",
        "vars_per_ctc_min": "1",
        "vars_per_ctc_max": "3",
        "prob_not": "0.3",
        "prob_and": "0.4",
        "prob_or": "0.2",
        "prob_implies": "0.2",
        "prob_equiv": "0.2",
    }
    data.update(overrides)
    return MultiDict(data)


def test_step4_rejects_invalid_boolean_operator_distribution():
    errors, _ = validate_step4_form(
        _valid_step4(
            prob_and="0.9",
            prob_or="0.9",
            prob_implies="0",
            prob_equiv="0",
        )
    )

    assert "boolop_sum" in errors


def test_step4_rejects_invalid_arithmetic_and_constraint_type_distributions():
    errors, _ = validate_step4_form(
        _valid_step4(
            prob_plus="0.9",
            prob_minus="0.9",
            prob_times="0",
            prob_div="0",
            prob_eq="0.2",
            prob_lt="0.2",
            prob_gt="0.2",
            prob_leq="0.2",
            prob_geq="0.2",
            ctc_dist_boolean="0.5",
            ctc_dist_integer="0.0",
            ctc_dist_real="0.0",
            ctc_dist_string="0.0",
        ),
        params_dict={"ARITHMETIC_LEVEL": True},
    )

    assert "arithmetic_sum" in errors
    assert "ctc_dist_sum" in errors


def _valid_step5_random(**overrides):
    data = {
        "random_attributes": "on",
        "min_attributes": "1",
        "max_attributes": "5",
        "dist_boolean": "1.0",
        "dist_integer": "0.0",
        "dist_real": "0.0",
        "dist_string": "0.0",
    }
    data.update(overrides)
    return MultiDict(data)


def test_step5_rejects_invalid_random_attribute_distribution():
    errors, _ = validate_step5_form(
        _valid_step5_random(
            dist_boolean="0.5",
            dist_integer="0.0",
            dist_real="0.0",
            dist_string="0.0",
        )
    )

    assert "attr_dist_sum" in errors


def test_validate_step3_reports_invalid_integer_fields():
    errors, _ = wizard.validate_step3_form(
        MultiDict(
            {
                "num_features_min": "invalid",
                "num_features_max": "invalid",
                "max_tree_depth": "invalid",
                "dist_optional": "0.25",
                "dist_mandatory": "0.25",
                "dist_alternative": "0.25",
                "dist_or": "0.25",
            }
        ),
        {},
    )

    assert errors["num_features_min"] == "Min. features must be an integer."
    assert errors["num_features_max"] == "Max. features must be an integer."


def test_validate_step4_reports_invalid_integer_fields():
    errors, _ = wizard.validate_step4_form(
        MultiDict(
            {
                "num_constraints_min": "invalid",
                "num_constraints_max": "invalid",
                "extra_constraint_repr": "1",
                "vars_per_ctc_min": "invalid",
                "vars_per_ctc_max": "invalid",
            }
        ),
        max_features=10,
        params_dict={},
    )

    assert errors["num_constraints_min"] == ("Min. constraints must be an integer.")
    assert errors["num_constraints_max"] == ("Max. constraints must be an integer.")
    assert errors["vars_per_ctc_min"] == ("Min. vars per constraint must be an integer.")
    assert errors["vars_per_ctc_max"] == ("Max. vars per constraint must be an integer.")


def test_validate_step5_reports_invalid_manual_attribute_fields():
    errors, _ = wizard.validate_step5_form(
        MultiDict(
            {
                "attr_name_0": "",
                "attr_type_0": "boolean",
                "attr_attach_prob_0": "0.5",
                "attr_value_true_0": "on",
                "attr_name_1": "number",
                "attr_type_1": "integer",
                "attr_use_in_constraints_1": "on",
                "attr_name_2": "real_value",
                "attr_type_2": "real",
                "attr_attach_prob_2": "invalid",
                "attr_min_value_2": "1",
                "attr_max_value_2": "2",
            }
        ),
        {
            "ARITHMETIC_LEVEL": True,
            "TYPE_LEVEL": True,
            "STRING_CONSTRAINTS": True,
        },
    )

    assert errors["attr_name_0"] == "Attribute name is required."
    assert errors["attr_attach_prob_1"] == ("Attach probability is required.")
    assert errors["attr_attach_prob_2"] == ("Attach probability must be a number.")
    assert errors["attr_minmax_1"] == "Min and Max are required."
