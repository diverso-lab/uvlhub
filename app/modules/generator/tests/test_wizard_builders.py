<<<<<<< HEAD
import pytest

from app.modules.generator.wizard_builders import (
=======
from app.modules.generator.wizard_builders import (
    build_step1_values,
    build_step2_values,
>>>>>>> 352a7cc12088baf77fcee5bfaaa24d6953cf95d3
    build_step3_values,
)


<<<<<<< HEAD
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
=======
def test_build_step1_values_defaults():
    values = build_step1_values({})
    assert values["num_models_val"] == 5
    assert values["seed"] == 42
    assert values["name_prefix"] == ""


def test_build_step2_values_defaults():
    values = build_step2_values({})
    assert values["boolean_level"] is True
    assert values["arithmetic_level"] is False
    assert values["type_level"] is False


def test_build_step3_handles_scalar_feature_cardinality():
    values = build_step3_values(
        {
            "MIN_FEATURE_CARDINALITY": 3,
            "MAX_FEATURE_CARDINALITY": 7,
        }
    )

    assert values["min_feature_cardinality"] == 3
    assert values["max_feature_cardinality"] == 7


def test_build_step3_handles_list_feature_cardinality():
    values = build_step3_values(
        {
            "MIN_FEATURE_CARDINALITY": [2],
            "MAX_FEATURE_CARDINALITY": [5],
        }
    )

    assert values["min_feature_cardinality"] == 2
    assert values["max_feature_cardinality"] == 5
>>>>>>> 352a7cc12088baf77fcee5bfaaa24d6953cf95d3
