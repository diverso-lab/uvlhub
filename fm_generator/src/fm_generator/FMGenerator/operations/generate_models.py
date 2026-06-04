import random

from flamapy.metamodels.fm_metamodel.models.feature_model import FeatureModel

from fm_generator.FMGenerator.models.config import Params
from fm_generator.FMGenerator.operations.attributes import (
    assign_manual_attributes,
    generate_random_attributes,
)
from fm_generator.FMGenerator.operations.constraints import add_constraints
from fm_generator.FMGenerator.operations.hierarchy import generate_hierarchy

SAT_SEED_STRIDE = 100000

__all__ = [
    "SAT_SEED_STRIDE",
    "generate_single_model",
]


def build_uvl_includes(params: Params) -> list[str]:
    includes: list[str] = []

    if getattr(params, "GROUP_CARDINALITY", False):
        includes.append("Boolean.group-cardinality")

    arithmetic_feature_cardinality = bool(getattr(params, "FEATURE_CARDINALITY", False))
    arithmetic_aggregate_functions = bool(getattr(params, "AGGREGATE_FUNCTIONS", False))

    if arithmetic_feature_cardinality and arithmetic_aggregate_functions:
        includes.append("Arithmetic.*")
    else:
        if arithmetic_aggregate_functions:
            includes.append("Arithmetic.aggregate-function")
        if arithmetic_feature_cardinality:
            includes.append("Arithmetic.feature-cardinality")

    if getattr(params, "TYPE_LEVEL", False) and getattr(params, "STRING_CONSTRAINTS", False):
        includes.append("Type.string-constraints")

    return includes


def generate_single_model(
    params: Params,
    index: int,
    attempt: int = 0,
) -> FeatureModel:
    seed_value = params.SEED + index + (attempt * SAT_SEED_STRIDE)
    random.seed(seed_value)

    fm, feats = generate_hierarchy(params)

    if params.RANDOM_ATTRIBUTES:
        generate_random_attributes(params, feats)
    else:
        assign_manual_attributes(params, feats)

    add_constraints(fm, feats, params)
    setattr(fm, "uvl_includes", build_uvl_includes(params))

    return fm
