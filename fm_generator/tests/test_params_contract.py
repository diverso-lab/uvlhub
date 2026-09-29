from dataclasses import fields

import pytest

from flamapy.metamodels.fm_generator.models import ConstraintsConfig, FmgeneratorModel


def _base_flat_params(**overrides):
    base = {
        "DIST_OPTIONAL": 0.3,
        "DIST_MANDATORY": 0.3,
        "DIST_ALTERNATIVE": 0.2,
        "DIST_OR": 0.2,
        "DIST_GROUP_CARDINALITY": 0.0,

        "PROB_AND": 0.4,
        "PROB_OR_CT": 0.2,
        "PROB_IMPLICATION": 0.2,
        "PROB_EQUIVALENCE": 0.2,

        "PROB_SUM": 0.4,
        "PROB_SUBSTRACT": 0.3,
        "PROB_MULTIPLY": 0.2,
        "PROB_DIVIDE": 0.1,

        "PROB_EQUALS": 0.2,
        "PROB_LESS": 0.2,
        "PROB_GREATER": 0.2,
        "PROB_LESS_EQUALS": 0.2,
        "PROB_GREATER_EQUALS": 0.2,

        "PROB_SUM_FUNCTION": 0.5,
        "PROB_AVG_FUNCTION": 0.5,
        "PROB_LEN_FUNCTION": 1.0,
    }
    base.update(overrides)
    return base


def test_wizard_referenced_params_keys_are_mapped_to_generator_model():
    params = _base_flat_params()
    model = FmgeneratorModel.from_flat_dict(params)

    assert model.hierarchy.dist_optional == params["DIST_OPTIONAL"]
    assert model.hierarchy.dist_mandatory == params["DIST_MANDATORY"]
    assert model.hierarchy.dist_alternative == params["DIST_ALTERNATIVE"]
    assert model.hierarchy.dist_or == params["DIST_OR"]
    assert model.hierarchy.dist_group_cardinality == params["DIST_GROUP_CARDINALITY"]

    assert model.constraints.prob_and == params["PROB_AND"]
    assert model.constraints.prob_or_ct == params["PROB_OR_CT"]
    assert model.constraints.prob_implication == params["PROB_IMPLICATION"]
    assert model.constraints.prob_equivalence == params["PROB_EQUIVALENCE"]

    assert model.constraints.prob_sum == params["PROB_SUM"]
    assert model.constraints.prob_substract == params["PROB_SUBSTRACT"]
    assert model.constraints.prob_multiply == params["PROB_MULTIPLY"]
    assert model.constraints.prob_divide == params["PROB_DIVIDE"]

    assert model.constraints.prob_equals == params["PROB_EQUALS"]
    assert model.constraints.prob_less == params["PROB_LESS"]
    assert model.constraints.prob_greater == params["PROB_GREATER"]
    assert model.constraints.prob_less_equals == params["PROB_LESS_EQUALS"]
    assert model.constraints.prob_greater_equals == params["PROB_GREATER_EQUALS"]

    assert model.constraints.prob_sum_function == params["PROB_SUM_FUNCTION"]
    assert model.constraints.prob_avg_function == params["PROB_AVG_FUNCTION"]
    assert model.constraints.prob_len_function == params["PROB_LEN_FUNCTION"]


def test_extra_constraint_representativeness_matches_integer_form_contract():
    field = next(
        f for f in fields(ConstraintsConfig)
        if f.name == "extra_constraint_representativeness"
    )

    assert field.type is int or field.type == "int"
    assert field.default == 1


def test_generator_model_defaults_are_valid_for_generation_contract():
    FmgeneratorModel()


def test_generator_model_rejects_relation_distribution_that_does_not_sum_to_one():
    with pytest.raises(ValueError):
        FmgeneratorModel.from_flat_dict(
            _base_flat_params(
                DIST_OPTIONAL=0.3,
                DIST_MANDATORY=0.3,
                DIST_ALTERNATIVE=0.2,
                DIST_OR=0.3,
                DIST_GROUP_CARDINALITY=0.0,
            )
        )


def test_generator_model_rejects_boolean_operator_distribution_that_does_not_sum_to_one():
    with pytest.raises(ValueError):
        FmgeneratorModel.from_flat_dict(
            _base_flat_params(
                PROB_AND=0.9,
                PROB_OR_CT=0.9,
                PROB_IMPLICATION=0.0,
                PROB_EQUIVALENCE=0.0,
            )
        )