from flamapy.core.discover import DiscoverMetamodels
from flamapy.metamodels.fm_metamodel.models.feature_model import FeatureModel

SATISFIABILITY_MAX_ATTEMPTS = 30
SAT_SEED_STRIDE = 100000
_SAT_BACKEND_WARNING_EMITTED = False


def is_model_satisfiable(feature_model: FeatureModel) -> bool:
    """Best-effort satisfiability check.

    In CPython we try PySAT. In Pyodide, python-sat/pysat is usually not
    available, so we avoid returning False just because the SAT backend cannot
    be loaded. Returning True in that case means: "generation may continue,
    but satisfiability could not be certified in this runtime".
    """
    global _SAT_BACKEND_WARNING_EMITTED

    try:
        dm = DiscoverMetamodels()
        sat_model = dm.use_transformation_m2m(feature_model, "pysat")
        operation = dm.get_operation(sat_model, "PySATSatisfiable")
        operation.execute(sat_model)
        return bool(operation.get_result())

    except ModuleNotFoundError as exc:
        missing = getattr(exc, "name", "")

        if missing in {"pysat", "pycryptosat"}:
            if not _SAT_BACKEND_WARNING_EMITTED:
                print(
                    "[SAT WARNING] PySAT backend is not available in this runtime; "
                    "continuing without SAT certification."
                )
                _SAT_BACKEND_WARNING_EMITTED = True
            return True

        raise

    except Exception as exc:
        msg = str(exc)

        if "No module named 'pysat'" in msg or "No module named pysat" in msg:
            if not _SAT_BACKEND_WARNING_EMITTED:
                print(
                    "[SAT WARNING] PySAT backend is not available in this runtime; "
                    "continuing without SAT certification."
                )
                _SAT_BACKEND_WARNING_EMITTED = True
            return True

        print(f"[SAT ERROR] PySAT satisfiability check failed: {exc}")
        return False
