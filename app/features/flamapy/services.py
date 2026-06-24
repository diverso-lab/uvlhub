import logging
import os
from typing import Any

from antlr4 import CommonTokenStream, FileStream
from antlr4.error.ErrorListener import ErrorListener
from flamapy.interfaces.python.flamapy_feature_model import FLAMAFeatureModel
from flamapy.metamodels.bdd_metamodel.operations import BDDMetrics
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD  # noqa
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.operations import FMMetrics
from flamapy.metamodels.pysat_metamodel.operations import PySATMetrics  # noqa
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat  # noqa
from uvl.UVLCustomLexer import UVLCustomLexer
from uvl.UVLPythonParser import UVLPythonParser

from app.features.hubfile.services import HubfileService
from app.managers.task_queue_manager import TaskQueueManager

logger = logging.getLogger(__name__)


class _UVLErrorListener(ErrorListener):
    """Collects lexer/parser syntax problems as human-readable messages."""

    def __init__(self):
        self.errors: list[str] = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        kind = "warning" if "\\t" in msg else "error"
        self.errors.append(f"The UVL has the following {kind} that prevents reading it: Line {line}:{column} - {msg}")


class FlamapyService:
    """Stateless service around the flamapy toolchain; owns no entity of its own."""

    def __init__(self):
        self.hubfile_service = HubfileService()

    @staticmethod
    def ide_url(hubfile) -> str:
        """URL that opens a hubfile in the Flamapy IDE (registered as a template global)."""
        return f"https://ide.flamapy.org/?import={hubfile.public_raw_url()}"

    def get_metrics(self, fm_model: FeatureModel) -> list[dict[str, Any]]:
        return FMMetrics().execute(fm_model).get_result()

    def get_analysis_results(self, fm_model: FeatureModel) -> list[dict[str, Any]]:
        return BDDMetrics().execute(fm_model).get_result()

    def transformed_file_path(self, file_id: int, extension: str, subdirectory: str) -> str | None:
        """Resolve the path of a transformed export for a hubfile, or None if it
        has not been generated yet."""
        hubfile = self.hubfile_service.get_or_404(file_id)
        dataset_dir = os.path.dirname(os.path.dirname(hubfile.get_path()))
        transformed_filename = os.path.basename(hubfile.get_path()).replace(".uvl", extension)
        path = os.path.join(dataset_dir, subdirectory, transformed_filename)
        return path if os.path.exists(path) else None

    def check_uvl_async(self, filepath: str):
        task = TaskQueueManager().enqueue_task("app.features.flamapy.tasks.check_uvl", filepath=filepath, timeout=5)
        return {"task_id": task.id}

    def check_uvl(self, filepath: str):
        error_listener = _UVLErrorListener()
        try:
            input_stream = FileStream(filepath)
            lexer = UVLCustomLexer(input_stream)
            lexer.removeErrorListeners()
            lexer.addErrorListener(error_listener)

            stream = CommonTokenStream(lexer)
            parser = UVLPythonParser(stream)
            parser.removeErrorListeners()
            parser.addErrorListener(error_listener)

            if error_listener.errors:
                logger.warning(f"[UVL Parser] Syntax errors detected: {error_listener.errors}")
                return {"errors": error_listener.errors}, 400

            try:
                FLAMAFeatureModel(filepath)
                return {"message": "Valid Model"}, 200
            except Exception as fe:
                logger.warning(f"[UVL Parser] FLAMA failed but will be ignored: {fe}")
                return {"message": "Valid Model (FLAMA transformation skipped due to unsupported attributes)"}, 200

        except Exception as e:
            logger.exception(f"[UVL Parser] Unexpected error during parsing: {e}")
            return {"error": f"Internal error during UVL check, {e}"}, 500
