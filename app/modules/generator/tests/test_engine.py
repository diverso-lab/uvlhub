from pathlib import Path

from flamapy.metamodels.fm_metamodel.models.feature_model import Feature, FeatureModel

from fm_generator.FMGenerator.models.config import Params
from fm_generator.FMGenerator.models.models import (
    build_output_filename,
    prepend_uvl_includes,
    FmgeneratorModel,
)


def test_prepend_uvl_includes_adds_include_block():
    result = prepend_uvl_includes(
        "features\n\tRoot\n",
        ["Boolean.group-cardinality", "Arithmetic.feature-cardinality"],
    )

    assert result.startswith("include\n")
    assert "\tBoolean.group-cardinality\n" in result
    assert "\tArithmetic.feature-cardinality\n" in result
    assert "features\n\tRoot\n" in result


def test_prepend_uvl_includes_does_nothing_without_includes():
    content = "features\n\tRoot\n"

    assert prepend_uvl_includes(content, []) == content


def test_build_output_filename_with_default_name():
    fm = FeatureModel(root=Feature("F0"))
    params = Params(NUM_MODELS=1, NAME_PREFIX="")

    filename = build_output_filename(fm, index=0, params=params)

    assert filename == "fm.uvl"


def test_build_output_filename_with_index_when_multiple_models():
    fm = FeatureModel(root=Feature("F0"))
    params = Params(NUM_MODELS=3, NAME_PREFIX="model")

    filename = build_output_filename(fm, index=2, params=params)

    assert filename == "model_2.uvl"


def test_build_output_filename_with_feature_and_constraint_suffixes():
    root = Feature("F0")
    fm = FeatureModel(root=root)
    fm.ctcs = [object(), object()]

    params = Params(
        NUM_MODELS=1,
        NAME_PREFIX="test",
        INCLUDE_FEATURE_COUNT_SUFFIX=True,
        INCLUDE_CONSTRAINT_COUNT_SUFFIX=True,
    )

    filename = build_output_filename(fm, index=0, params=params)

    assert filename.startswith("test_N")
    assert filename.endswith("_C2.uvl")


def test_generate_models_creates_expected_number_of_files(tmp_path):
    params = Params(
        NUM_MODELS=2,
        SEED=42,
        ENSURE_SATISFIABLE=False,
        NAME_PREFIX="generated",
        MIN_FEATURES=5,
        MAX_FEATURES=5,
        MAX_TREE_DEPTH=3,
        MIN_CONSTRAINTS=1,
        MAX_CONSTRAINTS=1,
        RANDOM_ATTRIBUTES=True,
        MIN_ATTRIBUTES=1,
        MAX_ATTRIBUTES=1,
    )

    generator = FmgeneratorModel(params)
    models = generator.generate_models(str(tmp_path))

    generated_files = list(Path(tmp_path).glob("*.uvl"))

    assert len(models) == 2
    assert len(generated_files) == 2
    assert (tmp_path / "generated_0.uvl").exists()
    assert (tmp_path / "generated_1.uvl").exists()