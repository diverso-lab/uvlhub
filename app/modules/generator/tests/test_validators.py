from werkzeug.datastructures import MultiDict

from app.modules.generator.validators import (
    validate_step1_form,
    validate_step2_form,
    validate_step3_form,
    validate_step4_form,
    validate_step5_form,
)
from app.modules.generator.wizard_persisters import safe_float

<<<<<<< HEAD
=======
# ─── safe_float helper ──────────────────────────────────────────────────
>>>>>>> 352a7cc12088baf77fcee5bfaaa24d6953cf95d3

def test_step1_rejects_batch_size_that_could_break_generation():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "1001", "seed": "42"}))

<<<<<<< HEAD
=======
def testsafe_float_accepts_dot():
    assert safe_float("0.5") == 0.5


def testsafe_float_accepts_spanish_comma():
    assert safe_float("0,5") == 0.5


def testsafe_float_falls_back_on_garbage():
    assert safe_float("nope", default=0.7) == 0.7


def testsafe_float_none_returns_default():
    assert safe_float(None, default=0.3) == 0.3


def testsafe_float_empty_returns_default():
    assert safe_float("  ", default=0.1) == 0.1


def testsafe_float_accepts_integer_strings():
    assert safe_float("5") == 5.0
    assert safe_float("0") == 0.0


def testsafe_float_accepts_negative():
    assert safe_float("-0.2") == -0.2


# ─── Step 1 · Batch ──────────────────────────────────────────────────────


def test_step1_happy_path():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "5", "seed": "42", "name_prefix": "fm"}))
    assert errors == {}


def test_step1_rejects_zero_models():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "0", "seed": "1"}))
>>>>>>> 352a7cc12088baf77fcee5bfaaa24d6953cf95d3
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


def test_step3_rejects_feature_bounds_that_make_tree_generation_impossible():
    errors, _ = validate_step3_form(_valid_step3(num_features_min="60", num_features_max="10"))

    assert "num_features_max" in errors


def test_step3_rejects_tree_depth_greater_than_available_features():
    errors, _ = validate_step3_form(_valid_step3(max_tree_depth="20", num_features_max="10"))

    assert "max_tree_depth" in errors


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


def test_step4_rejects_constraint_bounds_that_cannot_be_generated():
    errors, _ = validate_step4_form(_valid_step4(num_constraints_min="10", num_constraints_max="5"))

    assert "num_constraints_max" in errors


def test_step4_rejects_extra_constraint_representation_greater_than_ctc_size():
    errors, _ = validate_step4_form(_valid_step4(extra_constraint_repr="10", vars_per_ctc_max="3"))

    assert "extra_constraint_repr" in errors


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


def test_step5_rejects_random_attribute_bounds_that_cannot_be_generated():
    errors, _ = validate_step5_form(_valid_step5_random(min_attributes="10", max_attributes="5"))

    assert "max_attributes" in errors


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


def test_step5_rejects_manual_integer_attribute_with_invalid_range():
    form = MultiDict(
        {
            "attr_name_0": "Cost",
            "attr_type_0": "integer",
            "attr_attach_prob_0": "0.5",
            "attr_min_value_0": "10",
            "attr_max_value_0": "5",
        }
    )

    errors, _ = validate_step5_form(form)

    assert "attr_minmax_0" in errors


def test_step5_rejects_using_numeric_attribute_in_constraints_without_arithmetic():
    form = MultiDict(
        {
            "attr_name_0": "Cost",
            "attr_type_0": "integer",
            "attr_attach_prob_0": "0.5",
            "attr_min_value_0": "0",
            "attr_max_value_0": "10",
            "attr_use_in_constraints_0": "on",
        }
    )

    errors, _ = validate_step5_form(
        form,
        params_dict={"ARITHMETIC_LEVEL": False},
    )

    assert "attr_use_in_constraints_0" in errors
