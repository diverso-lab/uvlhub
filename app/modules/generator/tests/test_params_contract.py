import pytest

from fm_generator.FMGenerator.models.config import Params


def test_default_params_can_be_created():
    params = Params()

    assert params.BOOLEAN_LEVEL is True
    assert params.NUM_MODELS == 1
    assert params.SEED == 1


def test_type_level_forces_arithmetic_level():
    params = Params(
        TYPE_LEVEL=True,
        DIST_BOOLEAN=0.7,
        DIST_INTEGER=0.1,
        DIST_REAL=0.1,
        DIST_STRING=0.1,
    )

    assert params.TYPE_LEVEL is True
    assert params.ARITHMETIC_LEVEL is True
    assert params.BOOLEAN_LEVEL is True


def test_no_arithmetic_disables_feature_cardinality_and_aggregates():
    params = Params(
        ARITHMETIC_LEVEL=False,
        FEATURE_CARDINALITY=True,
        AGGREGATE_FUNCTIONS=True,
    )

    assert params.FEATURE_CARDINALITY is False
    assert params.AGGREGATE_FUNCTIONS is False


def test_invalid_relation_distribution_raises_error():
    with pytest.raises(ValueError):
        Params(
            DIST_OPTIONAL=0.5,
            DIST_MANDATORY=0.5,
            DIST_ALTERNATIVE=0.5,
            DIST_OR=0.0,
            DIST_GROUP_CARDINALITY=0.0,
        )


def test_ensure_satisfiable_forces_boolean_constraint_distribution():
    params = Params(
        ENSURE_SATISFIABLE=True,
        CTC_DIST_BOOLEAN=0.2,
        CTC_DIST_NUMERIC=0.3,
        CTC_DIST_AGGREGATE=0.3,
        CTC_DIST_STRING=0.2,
    )

    assert params.CTC_DIST_BOOLEAN == 1.0
    assert params.CTC_DIST_NUMERIC == 0.0
    assert params.CTC_DIST_AGGREGATE == 0.0
    assert params.CTC_DIST_STRING == 0.0
