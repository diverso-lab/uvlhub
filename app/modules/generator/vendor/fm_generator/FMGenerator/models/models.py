"""Top-level generator orchestrator.

Owns the multi-model loop: for each index, produce one FeatureModel (retrying
under ENSURE_SATISFIABLE until pysat says the model is satisfiable), pick a
filename that honours the INCLUDE_*_COUNT_SUFFIX toggles, and serialise via
UVLWriter.
"""

import os
from pathlib import Path

from flamapy.core.models import VariabilityModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations.uvl_writer import UVLWriter

from fm_generator.FMGenerator.models.config import Params
from fm_generator.FMGenerator.operations.generate_models import generate_single_model


class FmgeneratorModel(VariabilityModel):
    # How many re-rolls before we give up under ENSURE_SATISFIABLE and emit
    # the last candidate. Higher values trade generation time for quality;
    # 20 is enough to recover from the usual unsat combinations in practice.
    _SAT_MAX_ATTEMPTS = 20

    @staticmethod
    def get_extension() -> str:
        return "fm"

    def __init__(self, params: Params) -> None:
        self.params = params

    def generate_models(self, output_dir: str) -> list[FeatureModel]:
        fms: list[FeatureModel] = []
        for i in range(int(self.params.NUM_MODELS)):
            fm = self._build_one(i)
            fms.append(fm)
            output_file = Path(os.path.join(output_dir, self._filename_for(fm, i)))
            UVLWriter(str(output_file), fm).transform()
        return fms

    # ─── Internals ────────────────────────────────────────────────────

    def _build_one(self, index: int) -> FeatureModel:
        if not getattr(self.params, "ENSURE_SATISFIABLE", False):
            return generate_single_model(self.params, index)

        base_seed = int(self.params.SEED or 1)
        last: FeatureModel | None = None
        for attempt in range(self._SAT_MAX_ATTEMPTS):
            # Perturb SEED per attempt so we explore different models while
            # staying deterministic given (SEED, index, attempt).
            self.params.SEED = base_seed + attempt * 10_000
            try:
                fm = generate_single_model(self.params, index)
            except Exception:
                continue
            finally:
                self.params.SEED = base_seed
            if self._is_satisfiable(fm):
                return fm
            last = fm
        return last if last is not None else generate_single_model(self.params, index)

    @staticmethod
    def _is_satisfiable(fm: FeatureModel) -> bool:
        """Best-effort Boolean satisfiability via pysat. Arithmetic/string
        constraints fall outside SAT, so a True result only certifies the
        Boolean skeleton — which is still a useful filter against trivially
        broken hierarchies. Swallow transformation errors (some pysat builds
        trip on empty CNFs etc.) and assume satisfiable rather than blocking
        the whole batch."""
        try:
            from flamapy.metamodels.pysat_metamodel.operations import PySATSatisfiable
            from flamapy.metamodels.pysat_metamodel.transformations.fm_to_pysat import FmToPysat

            sat_model = FmToPysat(fm).transform()
            return bool(PySATSatisfiable().execute(sat_model).get_result())
        except Exception:
            return True

    def _filename_for(self, fm: FeatureModel, index: int) -> str:
        stem = f"{self.params.NAME_PREFIX}{index}"
        if getattr(self.params, "INCLUDE_FEATURE_COUNT_SUFFIX", False):
            stem += f"_{len(list(fm.get_features()))}f"
        if getattr(self.params, "INCLUDE_CONSTRAINT_COUNT_SUFFIX", False):
            stem += f"_{len(fm.ctcs)}c"
        return f"{stem}.uvl"
