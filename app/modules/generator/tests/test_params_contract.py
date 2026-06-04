from dataclasses import fields

import pytest

from fm_generator.FMGenerator.models.config import Params


def _params_field_names():
    return {f.name for f in fields(Params)}


def test_wizard_referenced_params_keys_exist_in_params_contract():
    referenced_keys = {
        "DIST_OPTIONAL",
        "DIST_MANDATORY",
        "DIST_ALTERNATIVE",
        "DIST_OR",
        "DIST_GROUP_CARDINALITY",
        "PROB_AND",
        "PROB_OR_CT",
        "PROB_IMPLICATION",
        "PROB_EQUIVALENCE",
        "PROB_SUM",
        "PROB_SUBSTRACT",
        "PROB_MULTIPLY",
        "PROB_DIVIDE",
        "PROB_EQUALS",
        "PROB_LESS",
        "PROB_GREATER",
        "PROB_LESS_EQUALS",
        "PROB_GREATER_EQUALS",
        "PROB_SUM_FUNCTION",
        "PROB_AVG_FUNCTION",
        "PROB_LEN_FUNCTION",
    }

    missing = referenced_keys - _params_field_names()

    assert not missing, f"Wizard references Params keys that do not exist: {missing}"


def test_extra_constraint_representativeness_matches_integer_form_contract():
    field = next(
        f for f in fields(Params)
        if f.name == "EXTRA_CONSTRAINT_REPRESENTATIVENESS"
    )

    assert field.type is int or field.type == "int"
    assert field.default == 1


def test_params_defaults_are_valid_for_generation_contract():
    Params()


def test_params_rejects_relation_distribution_that_does_not_sum_to_one():
    with pytest.raises(ValueError, match="Relation probabilities"):
        Params(
            DIST_OPTIONAL=0.3,
            DIST_MANDATORY=0.3,
            DIST_ALTERNATIVE=0.2,
            DIST_OR=0.3,
        )


def test_params_rejects_boolean_operator_distribution_that_does_not_sum_to_one():
    with pytest.raises(ValueError, match="PROB_AND"):
        Params(
            PROB_AND=0.9,
            PROB_OR_CT=0.9,
            PROB_IMPLICATION=0.0,
            PROB_EQUIVALENCE=0.0,
        )
