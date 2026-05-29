from app.modules.generator.wizard_builders import (
    build_step1_values,
    build_step2_values,
    build_step3_values,
)


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
