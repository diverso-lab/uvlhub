from pathlib import Path

from flamapy.core.discover import DiscoverMetamodels
from flamapy.core.models import VariabilityModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations.uvl_writer import UVLWriter

from fm_generator.FMGenerator.models.config import Params
from fm_generator.FMGenerator.operations.generate_models import generate_single_model

SATISFIABILITY_MAX_ATTEMPTS = 30


class FmgeneratorModel(VariabilityModel):
    @staticmethod
    def get_extension() -> str:
        return "fm"

    def __init__(self, params: Params) -> None:
        self.params = params

    def _prepend_uvl_includes(
        self,
        serialized_model: str,
        includes: list[str],
    ) -> str:
        if not includes:
            return serialized_model

        include_block = "include\n" + "\n".join(f"\t{inc}" for inc in includes) + "\n"
        return include_block + serialized_model

    def _build_output_filename(self, fm: FeatureModel, index: int) -> str:
        base_name = (getattr(self.params, "NAME_PREFIX", "") or "").strip() or "fm"

        include_features = bool(getattr(self.params, "INCLUDE_FEATURE_COUNT_SUFFIX", False))
        include_constraints = bool(getattr(self.params, "INCLUDE_CONSTRAINT_COUNT_SUFFIX", False))

        feature_count = len(list(fm.get_features()))
        constraint_count = len(getattr(fm, "ctcs", []))

        if include_features and include_constraints:
            return f"{base_name}_{feature_count}f_{constraint_count}c.uvl"

        if include_features:
            return f"{base_name}_{feature_count}f.uvl"

        if include_constraints:
            return f"{base_name}_{constraint_count}c.uvl"

        if int(getattr(self.params, "NUM_MODELS", 1)) > 1:
            return f"{base_name}_{index}.uvl"

        return f"{base_name}.uvl"

    def _filename_for(self, fm: FeatureModel, index: int) -> str:
        return self._build_output_filename(fm, index)

    def _build_one(self, index: int) -> FeatureModel:
        if not getattr(self.params, "ENSURE_SATISFIABLE", False):
            return generate_single_model(self.params, index)

        last_model = None

        for attempt in range(SATISFIABILITY_MAX_ATTEMPTS):
            fm = generate_single_model(self.params, index, attempt=attempt)
            last_model = fm

            if self._run_flamapy_satisfiability(fm):
                return fm

        if last_model is not None:
            return last_model

        raise RuntimeError(f"No se pudo generar ningún modelo para el índice {index}.")

    def generate_models(self, output_dir: str) -> list[FeatureModel]:
        fms = [self._build_one(i) for i in range(int(self.params.NUM_MODELS))]

        for i, fm in enumerate(fms):
            output_file = Path(output_dir) / self._build_output_filename(fm, i)

            serialized_model = UVLWriter(None, fm).transform()
            serialized_model = self._prepend_uvl_includes(
                serialized_model,
                getattr(fm, "uvl_includes", []),
            )

            with open(output_file, "w", encoding="utf8") as file:
                file.write(serialized_model)

        return fms

    def _run_flamapy_satisfiability(self, fm: FeatureModel) -> bool:
        try:
            dm = DiscoverMetamodels()
            sat_model = dm.use_transformation_m2m(fm, "pysat")
            operation = dm.get_operation(sat_model, "PySATSatisfiable")
            operation.execute(sat_model)
            return bool(operation.get_result())

        except ModuleNotFoundError as exc:
            missing = getattr(exc, "name", "")

            if missing in {"pysat", "pycryptosat"}:
                print(
                    "[SAT WARNING] PySAT backend is not available in this runtime; "
                    "continuing without SAT certification."
                )
                return True

            raise

        except Exception as exc:
            msg = str(exc)

            if "No module named 'pysat'" in msg or "No module named pysat" in msg:
                print(
                    "[SAT WARNING] PySAT backend is not available in this runtime; "
                    "continuing without SAT certification."
                )
                return True

            print(f"[SAT ERROR] PySATSatisfiable failed: {exc}")
            return False
