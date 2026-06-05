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
    "GenerateModels",
    "SAT_SEED_STRIDE",
]


class GenerateModels:
    """Operation responsible for generating random FeatureModel instances."""

    def __init__(self, params: Params) -> None:
        self.params = params

    def execute(self, index: int, attempt: int = 0) -> FeatureModel:
        self._seed_generation(index, attempt)

        fm, features = generate_hierarchy(self.params)
        self._assign_attributes(features)
        add_constraints(fm, features, self.params)

        setattr(fm, "uvl_includes", self._build_uvl_includes())

        return fm

    def _seed_generation(self, index: int, attempt: int) -> None:
        seed_value = self.params.SEED + index + (attempt * SAT_SEED_STRIDE)
        random.seed(seed_value)

    def _assign_attributes(self, features) -> None:
        if self.params.RANDOM_ATTRIBUTES:
            generate_random_attributes(self.params, features)
        else:
            assign_manual_attributes(self.params, features)

    def _build_uvl_includes(self) -> list[str]:
        includes: list[str] = []

        if getattr(self.params, "GROUP_CARDINALITY", False):
            includes.append("Boolean.group-cardinality")

        feature_cardinality = bool(getattr(self.params, "FEATURE_CARDINALITY", False))
        aggregate_functions = bool(getattr(self.params, "AGGREGATE_FUNCTIONS", False))

        if feature_cardinality and aggregate_functions:
            includes.append("Arithmetic.*")
        else:
            if aggregate_functions:
                includes.append("Arithmetic.aggregate-function")
            if feature_cardinality:
                includes.append("Arithmetic.feature-cardinality")

        if getattr(self.params, "TYPE_LEVEL", False) and getattr(
            self.params,
            "STRING_CONSTRAINTS",
            False,
        ):
            includes.append("Type.string-constraints")

        return includes
