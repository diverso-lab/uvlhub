import pytest

pytestmark = pytest.mark.unit

"""Unit tests for the per-step form validators.

The validators are pure functions (no DB, no request context) so we drive
each branch with parametrised inputs here. Covers every knob in every
step, both happy and sad paths.
"""

from werkzeug.datastructures import MultiDict

from app.features.generator.routes import (
    _safe_float,
    validate_step1_form,
    validate_step2_form,
    validate_step3_form,
    validate_step4_form,
    validate_step5_form,
    validate_step6_form,
)

# ─── _safe_float helper ──────────────────────────────────────────────────


def test_safe_float_accepts_dot():
    assert _safe_float("0.5") == 0.5


def test_safe_float_accepts_spanish_comma():
    assert _safe_float("0,5") == 0.5


def test_safe_float_falls_back_on_garbage():
    assert _safe_float("nope", default=0.7) == 0.7


def test_safe_float_none_returns_default():
    assert _safe_float(None, default=0.3) == 0.3


def test_safe_float_empty_returns_default():
    assert _safe_float("  ", default=0.1) == 0.1


def test_safe_float_accepts_integer_strings():
    assert _safe_float("5") == 5.0
    assert _safe_float("0") == 0.0


def test_safe_float_accepts_negative():
    assert _safe_float("-0.2") == -0.2


# ─── Step 1 · Batch ──────────────────────────────────────────────────────


def test_step1_happy_path():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "5", "seed": "42", "name_prefix": "fm"}))
    assert errors == {}


def test_step1_rejects_zero_models():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "0", "seed": "1"}))
    assert "num_models_val" in errors


def test_step1_rejects_negative_models():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "-1", "seed": "1"}))
    assert "num_models_val" in errors


def test_step1_rejects_1001_models():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "1001", "seed": "1"}))
    assert "num_models_val" in errors


def test_step1_accepts_1000_models():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "1000", "seed": "1"}))
    assert "num_models_val" not in errors


def test_step1_rejects_bad_num_models_string():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "abc", "seed": "1"}))
    assert "num_models_val" in errors


def test_step1_rejects_non_integer_seed():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "1", "seed": "abc"}))
    assert "seed" in errors


def test_step1_rejects_negative_seed():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "1", "seed": "-1"}))
    assert "seed" in errors


def test_step1_rejects_zero_seed():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "1", "seed": "0"}))
    assert "seed" in errors


# ─── Step 2 · Language levels ────────────────────────────────────────────


def test_step2_accepts_nothing_selected():
    errors, _ = validate_step2_form(MultiDict({}))
    assert errors == {}


def test_step2_accepts_arithmetic_only():
    errors, _ = validate_step2_form(MultiDict({"arithmetic_level": "on"}))
    assert errors == {}


def test_step2_accepts_type_only():
    errors, _ = validate_step2_form(MultiDict({"type_level": "on"}))
    assert errors == {}


def test_step2_accepts_all_majors_and_minors():
    errors, _ = validate_step2_form(
        MultiDict(
            {
                "arithmetic_level": "on",
                "type_level": "on",
                "feature_cardinality": "on",
                "aggregate_functions": "on",
                "string_constraints": "on",
                "group_cardinality": "on",
            }
        )
    )
    assert errors == {}


def test_step2_rejects_feature_cardinality_without_arithmetic():
    errors, _ = validate_step2_form(MultiDict({"feature_cardinality": "on"}))
    assert "feature_cardinality" in errors


def test_step2_rejects_aggregate_without_arithmetic():
    errors, _ = validate_step2_form(MultiDict({"aggregate_functions": "on"}))
    assert "aggregate_functions" in errors


def test_step2_rejects_string_constraints_without_type():
    errors, _ = validate_step2_form(MultiDict({"string_constraints": "on"}))
    assert "string_constraints" in errors


def test_step2_accepts_group_cardinality_without_any_major():
    # group_cardinality has no major dependency — it's an independent minor.
    errors, _ = validate_step2_form(MultiDict({"group_cardinality": "on"}))
    assert "group_cardinality" not in errors


# ─── Step 3 · Feature tree ──────────────────────────────────────────────


def _valid_step3(**overrides):
    base = {
        "num_features_min": "5",
        "num_features_max": "20",
        "max_tree_depth": "5",
        "dist_optional": "0.3",
        "dist_mandatory": "0.3",
        "dist_alternative": "0.2",
        "dist_or": "0.2",
    }
    base.update(overrides)
    return MultiDict(base)


def test_step3_happy_path():
    errors, _ = validate_step3_form(_valid_step3())
    assert errors == {}


def test_step3_rejects_min_gt_max_features():
    errors, _ = validate_step3_form(_valid_step3(num_features_min="30", num_features_max="10"))
    assert "num_features_max" in errors


def test_step3_rejects_zero_features():
    errors, _ = validate_step3_form(_valid_step3(num_features_min="0"))
    assert "num_features_min" in errors


def test_step3_rejects_depth_exceeding_max_features():
    errors, _ = validate_step3_form(_valid_step3(max_tree_depth="50", num_features_max="10"))
    assert "max_tree_depth" in errors


def test_step3_rejects_non_integer_depth():
    errors, _ = validate_step3_form(_valid_step3(max_tree_depth="abc"))
    assert "max_tree_depth" in errors


def test_step3_accepts_sum_within_tolerance():
    """Form-side tolerance is 1e-3 so slider-rounded values still validate."""
    errors, _ = validate_step3_form(
        _valid_step3(
            dist_optional="0.2502",
            dist_mandatory="0.2502",
            dist_alternative="0.2502",
            dist_or="0.2501",
        )
    )
    assert "rel_dist_total" not in errors


def test_step3_rejects_clearly_wrong_rel_sum():
    errors, _ = validate_step3_form(
        _valid_step3(
            dist_optional="0.9",
            dist_mandatory="0.9",
            dist_alternative="0",
            dist_or="0",
        )
    )
    assert "rel_dist_total" in errors


def test_step3_group_cardinality_requires_all_five_dists():
    """When group_cardinality is on, the 5-way sum (including
    dist_group_cardinality) must total 1.0."""
    errors, _ = validate_step3_form(
        _valid_step3(
            dist_optional="0.2",
            dist_mandatory="0.2",
            dist_alternative="0.2",
            dist_or="0.2",
            dist_group_cardinality="0.2",
        ),
        params_dict={"GROUP_CARDINALITY": True},
    )
    assert "rel_dist_total" not in errors


def test_step3_group_cardinality_min_gt_max():
    errors, _ = validate_step3_form(
        _valid_step3(
            dist_optional="0.2",
            dist_mandatory="0.2",
            dist_alternative="0.2",
            dist_or="0.2",
            dist_group_cardinality="0.2",
            group_cardinality_min="10",
            group_cardinality_max="5",
        ),
        params_dict={"GROUP_CARDINALITY": True},
    )
    assert "group_cardinality_max" in errors


def test_step3_feat_cardinality_prob_out_of_range():
    errors, _ = validate_step3_form(
        _valid_step3(prob_fc="1.5"),
        params_dict={"FEATURE_CARDINALITY": True},
    )
    assert "prob_fc" in errors


# ─── Step 4 · Constraints ───────────────────────────────────────────────


def _valid_step4(**overrides):
    base = {
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
    base.update(overrides)
    return MultiDict(base)


def test_step4_happy_path():
    errors, _ = validate_step4_form(_valid_step4())
    assert errors == {}


def test_step4_rejects_min_gt_max_constraints():
    errors, _ = validate_step4_form(_valid_step4(num_constraints_min="10", num_constraints_max="5"))
    assert "num_constraints_max" in errors


def test_step4_rejects_extra_repr_as_decimal():
    errors, _ = validate_step4_form(_valid_step4(extra_constraint_repr="0.5"))
    assert "extra_constraint_repr" in errors


def test_step4_rejects_extra_repr_gt_vars_max():
    errors, _ = validate_step4_form(_valid_step4(extra_constraint_repr="10", vars_per_ctc_max="3"))
    assert "extra_constraint_repr" in errors


def test_step4_boolops_sum_within_tolerance():
    errors, _ = validate_step4_form(
        _valid_step4(prob_and="0.3334", prob_or="0.3333", prob_implies="0.1667", prob_equiv="0.1666")
    )
    assert "boolop_sum" not in errors


def test_step4_boolops_sum_wildly_wrong():
    errors, _ = validate_step4_form(_valid_step4(prob_and="0.9", prob_or="0.9", prob_implies="0", prob_equiv="0"))
    assert "boolop_sum" in errors


def test_step4_arithmetic_ignored_when_level_off():
    """If Arithmetic isn't on, arithmetic probabilities shouldn't trigger
    any sum check."""
    errors, _ = validate_step4_form(
        _valid_step4(prob_plus="0", prob_minus="0", prob_times="0", prob_div="0"),
        params_dict={"ARITHMETIC_LEVEL": False},
    )
    assert "arithmetic_sum" not in errors


def test_step4_arithmetic_sum_required_when_level_on():
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
        ),
        params_dict={"ARITHMETIC_LEVEL": True},
    )
    assert "arithmetic_sum" in errors


def test_step4_comparison_sum_required_when_arithmetic_on():
    errors, _ = validate_step4_form(
        _valid_step4(
            prob_plus="0.7",
            prob_minus="0.2",
            prob_times="0.1",
            prob_div="0",
            prob_eq="0.5",
            prob_lt="0.5",
            prob_gt="0",
            prob_leq="0",
            prob_geq="0",
        ),
        params_dict={"ARITHMETIC_LEVEL": True},
    )
    assert "cmp_sum" not in errors  # 0.5+0.5 = 1.0 is fine


def test_step4_ctc_dist_required_when_any_level_on():
    errors, _ = validate_step4_form(
        _valid_step4(
            prob_plus="0.7",
            prob_minus="0.2",
            prob_times="0.1",
            prob_div="0",
            prob_eq="0.1",
            prob_lt="0.2",
            prob_gt="0.7",
            prob_leq="0",
            prob_geq="0",
            ctc_dist_boolean="0.5",
            ctc_dist_integer="0.0",
            ctc_dist_real="0.0",
            ctc_dist_string="0.0",
        ),
        params_dict={"ARITHMETIC_LEVEL": True},
    )
    # Active sum 0.5 ≠ 1.0 → should fail
    assert "ctc_dist_sum" in errors


def test_step4_ctc_dist_passes_when_sums_to_one():
    errors, _ = validate_step4_form(
        _valid_step4(
            prob_plus="0.7",
            prob_minus="0.2",
            prob_times="0.1",
            prob_div="0",
            prob_eq="0.1",
            prob_lt="0.2",
            prob_gt="0.7",
            prob_leq="0",
            prob_geq="0",
            ctc_dist_boolean="0.5",
            ctc_dist_integer="0.5",
            ctc_dist_real="0.0",
            ctc_dist_string="0.0",
        ),
        params_dict={"ARITHMETIC_LEVEL": True},
    )
    assert "ctc_dist_sum" not in errors


# ─── Step 5 · Attributes ────────────────────────────────────────────────


def _valid_step5_random(**overrides):
    base = {
        "random_attributes": "on",
        "min_attributes": "1",
        "max_attributes": "5",
        "dist_boolean": "1.0",
        "dist_integer": "0.0",
        "dist_real": "0.0",
        "dist_string": "0.0",
    }
    base.update(overrides)
    return MultiDict(base)


def test_step5_happy_path_random():
    errors, _ = validate_step5_form(_valid_step5_random())
    assert errors == {}


def test_step5_rejects_zero_min_attr():
    errors, _ = validate_step5_form(_valid_step5_random(min_attributes="0"))
    assert "min_attributes" in errors


def test_step5_rejects_too_many_attrs():
    errors, _ = validate_step5_form(_valid_step5_random(max_attributes="1001"))
    assert "max_attributes" in errors


def test_step5_rejects_min_gt_max_attrs():
    errors, _ = validate_step5_form(_valid_step5_random(min_attributes="10", max_attributes="5"))
    assert "max_attributes" in errors


def test_step5_attr_dist_sum_must_be_one():
    errors, _ = validate_step5_form(
        _valid_step5_random(
            dist_boolean="0.5",
            dist_integer="0.0",
            dist_real="0.0",
            dist_string="0.0",
        )
    )
    assert "attr_dist_sum" in errors


def test_step5_attr_dist_honours_gating():
    """When arithmetic is off, integer/real are pinned to 0 — so a dist of
    (bool=1, int=1, real=0, str=0) becomes (bool=1, int=0, real=0) = 1.0
    because int/real are masked out."""
    errors, _ = validate_step5_form(
        _valid_step5_random(dist_boolean="1.0", dist_integer="1.0"),
        params_dict={"ARITHMETIC_LEVEL": False, "TYPE_LEVEL": False},
    )
    assert "attr_dist_sum" not in errors


def test_step5_manual_mode_missing_name():
    form = MultiDict(
        {
            "attr_name_0": "",
            "attr_type_0": "boolean",
            "attr_attach_prob_0": "0.5",
            "attr_value_true_0": "on",
        }
    )
    errors, _ = validate_step5_form(form)
    assert "attr_name_0" in errors


def test_step5_manual_mode_boolean_needs_value():
    form = MultiDict(
        {
            "attr_name_0": "A",
            "attr_type_0": "boolean",
            "attr_attach_prob_0": "0.5",
        }
    )
    errors, _ = validate_step5_form(form)
    assert "attr_value_bool_0" in errors


def test_step5_manual_mode_integer_needs_range():
    form = MultiDict(
        {
            "attr_name_0": "A",
            "attr_type_0": "integer",
            "attr_attach_prob_0": "0.5",
        }
    )
    errors, _ = validate_step5_form(form)
    assert "attr_minmax_0" in errors


def test_step5_manual_mode_min_gt_max():
    form = MultiDict(
        {
            "attr_name_0": "A",
            "attr_type_0": "integer",
            "attr_attach_prob_0": "0.5",
            "attr_min_value_0": "10",
            "attr_max_value_0": "5",
        }
    )
    errors, _ = validate_step5_form(form)
    assert "attr_minmax_0" in errors


def test_step5_manual_mode_bad_attach_prob():
    form = MultiDict(
        {
            "attr_name_0": "A",
            "attr_type_0": "boolean",
            "attr_attach_prob_0": "1.5",
            "attr_value_true_0": "on",
        }
    )
    errors, _ = validate_step5_form(form)
    assert "attr_attach_prob_0" in errors


def test_step5_manual_mode_use_in_ctc_integer_requires_arithmetic():
    form = MultiDict(
        {
            "attr_name_0": "A",
            "attr_type_0": "integer",
            "attr_attach_prob_0": "0.5",
            "attr_min_value_0": "0",
            "attr_max_value_0": "10",
            "attr_use_in_constraints_0": "on",
        }
    )
    errors, _ = validate_step5_form(form, params_dict={"ARITHMETIC_LEVEL": False})
    assert "attr_use_in_constraints_0" in errors


# ─── Step 6 · Output ────────────────────────────────────────────────────


def test_step6_empty_is_fine():
    errors, _ = validate_step6_form(MultiDict({}))
    assert errors == {}


def test_step6_reads_ensure_satisfiable():
    _, values = validate_step6_form(MultiDict({"ensure_satisfiable": "on"}))
    assert values["ensure_satisfiable"] is True


def test_step6_reads_feature_suffix():
    _, values = validate_step6_form(MultiDict({"feature_count_suffix": "on"}))
    assert values["feature_count_suffix"] is True


def test_step6_reads_constraint_suffix():
    _, values = validate_step6_form(MultiDict({"constraint_count_suffix": "on"}))
    assert values["constraint_count_suffix"] is True


def test_step6_defaults_all_false():
    _, values = validate_step6_form(MultiDict({}))
    assert values == {
        "ensure_satisfiable": False,
        "feature_count_suffix": False,
        "constraint_count_suffix": False,
    }
