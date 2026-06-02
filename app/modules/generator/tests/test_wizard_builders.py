from app.modules.generator.wizard_builders import build_step3_values


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


def test_build_step3_handles_empty_feature_cardinality_list():
    values = build_step3_values(
        {
            "MIN_FEATURE_CARDINALITY": [],
            "MAX_FEATURE_CARDINALITY": [],
        }
    )

    assert values["min_feature_cardinality"] == 2
    assert values["max_feature_cardinality"] == 5