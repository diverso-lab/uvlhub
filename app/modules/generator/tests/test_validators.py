"""Unit tests for the per-step form validators.

These run against the pure validator functions (no DB, no request context)
and drive each branch with parametrised inputs. A regression here catches
the kind of locale/tolerance bugs that reached production.
"""
from werkzeug.datastructures import MultiDict

from app.modules.generator.routes import (
    _safe_float,
    validate_step1_form,
    validate_step2_form,
    validate_step3_form,
)


# ── _safe_float ───────────────────────────────────────────────────────────

def test_safe_float_accepts_dot():
    assert _safe_float("0.5") == 0.5


def test_safe_float_accepts_spanish_comma():
    """Chrome/Firefox on es_ES locale submit <input type=number> with commas."""
    assert _safe_float("0,5") == 0.5


def test_safe_float_falls_back_on_garbage():
    assert _safe_float("nope", default=0.7) == 0.7


def test_safe_float_none_returns_default():
    assert _safe_float(None, default=0.3) == 0.3


def test_safe_float_empty_returns_default():
    assert _safe_float("  ", default=0.1) == 0.1


# ── step1 ─────────────────────────────────────────────────────────────────

def test_step1_happy_path():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "5", "seed": "42"}))
    assert errors == {}


def test_step1_rejects_zero_models():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "0", "seed": "1"}))
    assert "num_models_val" in errors


def test_step1_rejects_non_integer_seed():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "1", "seed": "abc"}))
    assert "seed" in errors


def test_step1_rejects_negative_seed():
    errors, _ = validate_step1_form(MultiDict({"num_models_val": "1", "seed": "-1"}))
    assert "seed" in errors


# ── step2 ─────────────────────────────────────────────────────────────────

def _valid_step2(**overrides):
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


def test_step2_happy_path():
    errors, _ = validate_step2_form(_valid_step2())
    assert errors == {}


def test_step2_rejects_min_gt_max():
    errors, _ = validate_step2_form(
        _valid_step2(num_features_min="30", num_features_max="10")
    )
    assert "num_features_max" in errors


def test_step2_accepts_sum_within_tolerance():
    """Form-side tolerance is 1e-3 so users can still advance with rounded values.

    The route renormalises server-side before handing the values to Params,
    which has the strict 1e-6 check — so a 1.0007 coming from the slider
    must not block here.
    """
    errors, _ = validate_step2_form(
        _valid_step2(
            dist_optional="0.2502",
            dist_mandatory="0.2502",
            dist_alternative="0.2502",
            dist_or="0.2501",
        )
    )
    # 0.2502*3 + 0.2501 = 1.0007 → within 1e-3 tolerance
    assert "rel_dist_total" not in errors


def test_step2_rejects_clearly_wrong_sum():
    errors, _ = validate_step2_form(
        _valid_step2(dist_optional="0.9", dist_mandatory="0.9", dist_alternative="0", dist_or="0")
    )
    assert "rel_dist_total" in errors
    assert "Current sum" in errors["rel_dist_total"]


# ── step3 ─────────────────────────────────────────────────────────────────

def _valid_step3(**overrides):
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


def test_step3_happy_path():
    errors, _ = validate_step3_form(_valid_step3())
    assert errors == {}


def test_step3_rejects_extra_constraint_repr_as_decimal():
    """The vendor default used to be 0.5 (float). The route now coerces to
    int, but the validator must still complain if the user types a decimal."""
    errors, _ = validate_step3_form(_valid_step3(extra_constraint_repr="0.5"))
    assert "extra_constraint_repr" in errors


def test_step3_rejects_extra_constraint_repr_gt_vars_max():
    errors, _ = validate_step3_form(
        _valid_step3(extra_constraint_repr="10", vars_per_ctc_max="3")
    )
    assert "extra_constraint_repr" in errors


def test_step3_boolops_sum_within_tolerance():
    """Same story as step2: 1.0007 from the slider must pass the form check."""
    errors, _ = validate_step3_form(
        _valid_step3(prob_and="0.3334", prob_or="0.3333", prob_implies="0.1667", prob_equiv="0.1666")
    )
    assert "boolop_sum" not in errors


def test_step3_boolops_sum_wildly_wrong():
    errors, _ = validate_step3_form(
        _valid_step3(prob_and="0.9", prob_or="0.9", prob_implies="0", prob_equiv="0")
    )
    assert "boolop_sum" in errors
    assert "Current sum" in errors["boolop_sum"]


def test_step3_arithmetic_only_when_level_enabled():
    """If arithmetic_level is off, the arithmetic-sum check should not fire."""
    errors, _ = validate_step3_form(
        _valid_step3(prob_plus="0", prob_minus="0", prob_times="0", prob_div="0")
    )
    assert "arithmetic_sum" not in errors


def test_step3_arithmetic_sum_enforced_when_level_on():
    errors, _ = validate_step3_form(
        _valid_step3(
            arithmetic_level="on",
            prob_plus="0.9", prob_minus="0.9", prob_times="0", prob_div="0",
        )
    )
    assert "arithmetic_sum" in errors
