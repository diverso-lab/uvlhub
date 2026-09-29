import pytest

from app.features.generator.wizard import (
    build_step1_values,
    build_step2_values,
    build_step3_values,
    build_step4_values,
    build_step5_values,
    build_step6_values,
    first_or_value,
)

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "min_cardinality,max_cardinality,expected_min,expected_max",
    [
        (3, 7, 3, 7),
        ([2], [5], 2, 5),
        ([], [], 2, 5),
    ],
)
def test_build_step3_normalises_feature_cardinality_values(
    min_cardinality,
    max_cardinality,
    expected_min,
    expected_max,
):
    values = build_step3_values(
        {
            "MIN_FEATURE_CARDINALITY": min_cardinality,
            "MAX_FEATURE_CARDINALITY": max_cardinality,
        }
    )

    assert values["min_feature_cardinality"] == expected_min
    assert values["max_feature_cardinality"] == expected_max


def test_build_step3_preserves_group_cardinality_distribution_when_enabled():
    values = build_step3_values(
        {
            "GROUP_CARDINALITY": True,
            "DIST_OPTIONAL": 0.2,
            "DIST_MANDATORY": 0.2,
            "DIST_ALTERNATIVE": 0.2,
            "DIST_OR": 0.2,
            "DIST_GROUP_CARDINALITY": 0.2,
        }
    )

    total = (
        values["dist_optional"]
        + values["dist_mandatory"]
        + values["dist_alternative"]
        + values["dist_or"]
        + values["dist_group_cardinality"]
    )

    assert values["group_cardinality"] is True
    assert total == 1.0


@pytest.mark.parametrize(
    ("value", "default", "expected"),
    [
        ([1, 2], 9, 1),
        ((3, 4), 9, 3),
        ([], 9, 9),
        (None, 9, 9),
        ("value", 9, "value"),
    ],
)
def test_first_or_value_handles_lists_tuples_none_and_scalars(
    value,
    default,
    expected,
):
    assert first_or_value(value, default) == expected


def test_build_step1_values_uses_saved_parameters():
    values = build_step1_values(
        {
            "NUM_MODELS": 8,
            "SEED": 123,
            "NAME_PREFIX": "custom",
        }
    )

    assert values == {
        "num_models_val": 8,
        "seed": 123,
        "name_prefix": "custom",
    }


def test_build_step1_values_uses_defaults_when_parameters_are_missing():
    values = build_step1_values({})

    assert values == {
        "num_models_val": 5,
        "seed": 42,
        "name_prefix": "",
    }


def test_build_step2_values_reads_all_level_flags():
    values = build_step2_values(
        {
            "ARITHMETIC_LEVEL": True,
            "TYPE_LEVEL": True,
            "FEATURE_CARDINALITY": True,
            "AGGREGATE_FUNCTIONS": True,
            "STRING_CONSTRAINTS": True,
            "GROUP_CARDINALITY": True,
        }
    )

    assert values == {
        "boolean_level": True,
        "arithmetic_level": True,
        "type_level": True,
        "feature_cardinality": True,
        "aggregate_functions": True,
        "string_constraints": True,
        "group_cardinality": True,
    }


def test_build_step4_values_uses_defaults_and_clamps_max_variables(test_client):
    with test_client.application.test_request_context():
        from flask import session

        session.clear()

        values = build_step4_values(
            {
                "MAX_FEATURES": 5,
                "EXTRA_CONSTRAINT_REPRESENTATIVENESS": "invalid",
            }
        )

        assert values["extra_constraint_repr"] == 1
        assert values["vars_per_ctc_max"] == "5"
        assert values["prob_len"] == 0.0
        assert values["max_features"] == 5


def test_build_step4_values_restores_saved_arithmetic_and_string_values(test_client):
    with test_client.application.test_request_context():
        from flask import session

        session["wizard"] = {
            "4": {
                "prob_plus": "0.4",
                "prob_len": "0.9",
                "vars_per_ctc_max": "invalid",
            }
        }

        values = build_step4_values(
            {
                "MAX_FEATURES": 4,
                "MAX_VARS_PER_CONSTRAINT": 10,
                "TYPE_LEVEL": True,
                "STRING_CONSTRAINTS": True,
                "PROB_SUM": 0.4,
                "PROB_LEN_FUNCTION": 0.9,
            }
        )

        assert values["prob_plus"] == "0.4"
        assert values["prob_len"] == "0.9"
        assert values["vars_per_ctc_max"] == "4"
        assert values["type_level"] is True
        assert values["string_constraints"] is True


def test_build_step5_values_merges_saved_state(test_client):
    with test_client.application.test_request_context():
        from flask import session

        session["wizard"] = {
            "5": {
                "max_attributes": "9",
            }
        }

        values = build_step5_values(
            {
                "RANDOM_ATTRIBUTES": False,
                "MIN_ATTRIBUTES": 1,
                "MAX_ATTRIBUTES": 5,
            }
        )

        assert values["random_attributes"] is False
        assert values["min_attributes"] == 1
        assert values["max_attributes"] == "9"


def test_build_step6_values_reads_output_options(test_client):
    with test_client.application.test_request_context():
        from flask import session

        session.clear()

        values = build_step6_values(
            {
                "ENSURE_SATISFIABLE": True,
                "INCLUDE_FEATURE_COUNT_SUFFIX": True,
                "INCLUDE_CONSTRAINT_COUNT_SUFFIX": False,
            }
        )

        assert values == {
            "ensure_satisfiable": True,
            "feature_count_suffix": True,
            "constraint_count_suffix": False,
        }
