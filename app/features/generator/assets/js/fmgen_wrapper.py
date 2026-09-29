# fmgen_wrapper.py — runs inside Pyodide and returns generated UVL strings.
#
# Two entry points:
#
#   generate_models(params_json)               -> JSON list of UVL strings
#   generate_one_model(params_json, index)     -> JSON object {filename, content}

import json

from flamapy.metamodels.fm_generator.models import FmgeneratorModel
from flamapy.metamodels.fm_generator.operations import GenerateFeatureModel
from flamapy.metamodels.fm_metamodel.models.feature_model import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations.uvl_writer import UVLWriter


def _prepend_uvl_includes(serialized_model: str, includes: list[str]) -> str:
    if not includes:
        return serialized_model

    include_block = "include\n" + "\n".join(f"\t{inc}" for inc in includes) + "\n"
    return include_block + serialized_model


def _serialize_uvl(fm: FeatureModel) -> str:
    serialized_model = UVLWriter(None, fm).transform()
    return _prepend_uvl_includes(
        serialized_model,
        getattr(fm, "uvl_includes", []),
    )


def _filename_for(model: FmgeneratorModel, fm: FeatureModel, index: int) -> str:
    base_name = (model.naming.name_prefix or "").strip() or "fm"

    include_features = model.naming.include_feature_count_suffix
    include_constraints = model.naming.include_constraint_count_suffix

    feature_count = len(list(fm.get_features()))
    constraint_count = len(getattr(fm, "ctcs", []))

    if include_features and include_constraints:
        return f"{base_name}_{feature_count}f_{constraint_count}c.uvl"

    if include_features:
        return f"{base_name}_{feature_count}f.uvl"

    if include_constraints:
        return f"{base_name}_{constraint_count}c.uvl"

    if model.num_models > 1:
        return f"{base_name}_{index}.uvl"

    return f"{base_name}.uvl"


def _generate_feature_model(
    model: FmgeneratorModel,
    index: int,
    attempt: int = 0,
) -> FeatureModel:

    operation = GenerateFeatureModel()

    operation.execute(
        model=model,
        index=index,
        attempt=attempt,
    )

    return operation.get_result()


def _build_one(model: FmgeneratorModel, index: int) -> FeatureModel:
    return _generate_feature_model(
        model,
        index,
    )


def generate_models(params_json: str) -> str:
    """Generate the full batch and return every UVL as a JSON list."""
    params_dict = json.loads(params_json)
    model = FmgeneratorModel.from_flat_dict(params_dict)

    results = []

    for index in range(model.num_models):
        fm = _build_one(model, index)
        results.append(_serialize_uvl(fm))

    return json.dumps(results)


def generate_one_model(params_json: str, index: int) -> str:
    """Generate the model at `index` and return {filename, content} as JSON."""
    params_dict = json.loads(params_json)
    model = FmgeneratorModel.from_flat_dict(params_dict)

    fm = _build_one(model, int(index))
    filename = _filename_for(model, fm, int(index))
    content = _serialize_uvl(fm)

    return json.dumps(
        {
            "filename": filename,
            "content": content,
            "features": len(list(fm.get_features())),
            "constraints": len(fm.ctcs),
        }
    )
