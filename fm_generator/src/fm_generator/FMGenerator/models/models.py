import os
from pathlib import Path

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations.uvl_writer import UVLWriter

from fm_generator.FMGenerator.models.config import Params
from fm_generator.FMGenerator.operations.generate_models import (
    SATISFIABILITY_MAX_ATTEMPTS,
    generate_single_model,
    is_model_satisfiable,
)


def prepend_uvl_includes(serialized_model: str, includes: list[str]) -> str:
    if not includes:
        return serialized_model

    include_block = "include\n" + "\n".join(f"\t{inc}" for inc in includes) + "\n"
    return include_block + serialized_model


def build_output_filename(fm: FeatureModel, index: int, params: Params) -> str:
    base_name = (params.NAME_PREFIX or "").strip() or "fm"
    parts = [base_name]

    if int(params.NUM_MODELS) > 1:
        parts.append(str(index))

    if getattr(params, "INCLUDE_FEATURE_COUNT_SUFFIX", False):
        parts.append(f"N{len(fm.get_features())}")

    if getattr(params, "INCLUDE_CONSTRAINT_COUNT_SUFFIX", False):
        parts.append(f"C{len(getattr(fm, 'ctcs', []))}")

    return "_".join(parts) + ".uvl"


class FmgeneratorModel(VariabilityModel):
    @staticmethod
    def get_extension() -> str:
        return "fm"

    def __init__(self, params: Params) -> None:
        self.params = params

    def _build_one(self, index: int) -> FeatureModel:
        if not getattr(self.params, "ENSURE_SATISFIABLE", False):
            return generate_single_model(self.params, index)

        last_model = None

        for attempt in range(SATISFIABILITY_MAX_ATTEMPTS):
            fm = generate_single_model(self.params, index, attempt=attempt)
            last_model = fm

            if is_model_satisfiable(fm):
                return fm

        if last_model is not None:
            return last_model

        raise RuntimeError(
            f"No se pudo generar ningún modelo para el índice {index}."
        )

    def _filename_for(self, fm: FeatureModel, index: int) -> str:
        return build_output_filename(fm, index, self.params)

    def generate_models(self, output_dir: str) -> list[FeatureModel]:
        fms = [self._build_one(i) for i in range(int(self.params.NUM_MODELS))]

        for i, fm in enumerate(fms):
            output_file = Path(os.path.join(output_dir, self._filename_for(fm, i)))

            serialized_model = UVLWriter(None, fm).transform()
            serialized_model = prepend_uvl_includes(
                serialized_model,
                getattr(fm, "uvl_includes", []),
            )

            with open(output_file, "w", encoding="utf8") as file:
                file.write(serialized_model)

        return fms