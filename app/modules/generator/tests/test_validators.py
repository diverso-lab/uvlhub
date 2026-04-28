from werkzeug.datastructures import MultiDict

from app.modules.generator.routes import (
    resolve_use_in_constraints,
    validate_step1_form,
    validate_step2_form,
    validate_step3_form,
    validate_step4_form,
)


def test_step1_valid_form_has_no_errors():
    form = MultiDict(
        {
            "num_models_val": "3",
            "seed": "42",
            "name_prefix": "fm",
        }
    )

    errors, values = validate_step1_form(form)

    assert errors == {}
    assert values["num_models_val"] == "3"
    assert values["seed"] == "42"


def test_step1_rejects_invalid_num_models_and_seed():
    form = MultiDict(
        {
            "num_models_val": "0",
            "seed": "-1",
        }
    )

    errors, _ = validate_step1_form(form)

    assert "num_models_val" in errors
    assert "seed" in errors


def test_step2_rejects_invalid_feature_range():
    form = MultiDict(
        {
            "num_features_min": "20",
            "num_features_max": "10",
            "max_tree_depth": "5",
            "dist_optional": "0.25",
            "dist_mandatory": "0.25",
            "dist_alternative": "0.25",
            "dist_or": "0.25",
        }
    )

    errors, _ = validate_step2_form(form, params_dict={})

    assert "num_features_max" in errors


def test_step2_rejects_aggregate_functions_when_ensure_sat_enabled():
    form = MultiDict(
        {
            "num_features_min": "10",
            "num_features_max": "20",
            "max_tree_depth": "5",
            "aggregate_functions": "on",
            "dist_optional": "0.25",
            "dist_mandatory": "0.25",
            "dist_alternative": "0.25",
            "dist_or": "0.25",
        }
    )

    errors, _ = validate_step2_form(
        form,
        params_dict={"ENSURE_SATISFIABLE": True},
    )

    assert "aggregate_functions" in errors


def test_step3_rejects_ecr_greater_than_max_vars():
    form = MultiDict(
        {
            "num_constraints_min": "1",
            "num_constraints_max": "5",
            "extra_constraint_repr": "6",
            "vars_per_ctc_min": "2",
            "vars_per_ctc_max": "4",
            "prob_not": "0.1",
            "prob_and": "0.4",
            "prob_or": "0.2",
            "prob_implies": "0.2",
            "prob_equiv": "0.2",
        }
    )

    errors, _ = validate_step3_form(form, max_features=10, params_dict={})

    assert "extra_constraint_repr" in errors


def test_step3_accepts_ecr_equal_to_max_vars():
    form = MultiDict(
        {
            "num_constraints_min": "1",
            "num_constraints_max": "5",
            "extra_constraint_repr": "4",
            "vars_per_ctc_min": "2",
            "vars_per_ctc_max": "4",
            "prob_not": "0.1",
            "prob_and": "0.4",
            "prob_or": "0.2",
            "prob_implies": "0.2",
            "prob_equiv": "0.2",
        }
    )

    errors, _ = validate_step3_form(form, max_features=10, params_dict={})

    assert "extra_constraint_repr" not in errors


def test_step4_random_attributes_valid_form():
    form = MultiDict(
        {
            "random_attributes": "on",
            "min_attributes": "1",
            "max_attributes": "5",
        }
    )

    errors, values = validate_step4_form(form, params_dict={})

    assert errors == {}
    assert values["random_attributes"] is True


def test_step4_manual_boolean_requires_at_least_one_value():
    form = MultiDict(
        {
            "attr_name_0": "Color",
            "attr_type_0": "boolean",
            "attr_attach_prob_0": "0.5",
        }
    )

    errors, _ = validate_step4_form(form, params_dict={})

    assert "attr_value_bool_0" in errors


def test_resolve_use_in_constraints_disabled_when_ensure_sat():
    result = resolve_use_in_constraints(
        raw_use_in_constraints=True,
        type_="boolean",
        params_dict={"ENSURE_SATISFIABLE": True},
    )

    assert result is False


def test_resolve_use_in_constraints_integer_requires_arithmetic_level():
    result = resolve_use_in_constraints(
        raw_use_in_constraints=True,
        type_="integer",
        params_dict={
            "ENSURE_SATISFIABLE": False,
            "ARITHMETIC_LEVEL": False,
        },
    )

    assert result is False
