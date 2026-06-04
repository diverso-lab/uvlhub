import pytest

from app.modules.generator.wizard_builders import (
    build_step3_values,
    build_step4_values,
)


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


def test_build_step4_converts_extra_constraint_repr_to_valid_integer():
    values = build_step4_values(
        {
            "EXTRA_CONSTRAINT_REPRESENTATIVENESS": 0.5,
            "MAX_FEATURES": 20,
        }
    )

    assert values["extra_constraint_repr"] == 1
