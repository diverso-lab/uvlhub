from flamapy.core.models import VariabilityModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from fm_generator.FMGenerator.operations.generate_models import (
    generate_single_model,
    is_model_satisfiable,
    SATISFIABILITY_MAX_ATTEMPTS,
)
from fm_generator.FMGenerator.models.config import Params
from pathlib import Path
from flamapy.metamodels.fm_metamodel.transformations.uvl_writer import UVLWriter
import os


def prepend_uvl_includes(serialized_model: str, includes: list[str]) -> str:
    if not includes:
        return serialized_model

    include_block = "include\n" + \
        "\n".join(f"\t{inc}" for inc in includes) + "\n"
    return include_block + serialized_model


def build_output_filename(fm: FeatureModel, index: int, params: Params) -> str:
    base_name = (params.NAME_PREFIX or "").strip()

    if not base_name:
        base_name = "fm"

    parts = [base_name]

    if params.NUM_MODELS > 1:
        parts.append(str(index))

    if getattr(params, "INCLUDE_FEATURE_COUNT_SUFFIX", False):
        num_features = len(fm.get_features())
        parts.append(f"N{num_features}")

    if getattr(params, "INCLUDE_CONSTRAINT_COUNT_SUFFIX", False):
        num_constraints = len(getattr(fm, "ctcs", []))
        parts.append(f"C{num_constraints}")

    return "_".join(parts) + ".uvl"


class FmgeneratorModel(VariabilityModel):
    @staticmethod
    def get_extension() -> str:
        return "fm"

    def __init__(self, params: Params) -> None:
        self.params = params

    def _generate_one_model(self, index: int) -> FeatureModel:
        if not self.params.ENSURE_SATISFIABLE:
            return generate_single_model(self.params, index)

        last_model = None

        for attempt in range(SATISFIABILITY_MAX_ATTEMPTS):
            fm = generate_single_model(self.params, index, attempt=attempt)
            last_model = fm

            if is_model_satisfiable(fm):
                print(
                    f"Modelo {index}: modelo booleanamente satisfacible encontrado en intento " f"{
                        attempt + 1}/{SATISFIABILITY_MAX_ATTEMPTS}")
                return fm

        raise RuntimeError(
            f"No se pudo generar un modelo booleanamente satisfacible para el índice {index} "
            f"tras {SATISFIABILITY_MAX_ATTEMPTS} intentos."
        )

    def generate_models(self, output_dir: str) -> list[FeatureModel]:
        print(self.params)

        fms = [self._generate_one_model(i)
               for i in range(self.params.NUM_MODELS)]

        for i in range(len(fms)):
            filename = build_output_filename(fms[i], i, self.params)
            output_file = Path(os.path.join(output_dir, filename))

            serialized_model = UVLWriter(None, fms[i]).transform()
            serialized_model = prepend_uvl_includes(
                serialized_model,
                getattr(fms[i], "uvl_includes", [])
            )

            with open(output_file, "w", encoding="utf8") as file:
                file.write(serialized_model)

            print(f"Modelo generado y exportado en: {output_file}")

        return fms
