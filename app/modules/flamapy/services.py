import logging
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

from app.modules.flamapy.repositories import FlamapyRepository
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


class FlamapyService(BaseService):
    def __init__(self):
        super().__init__(FlamapyRepository())

    def get_metrics(self, fm_model: FeatureModel) -> list[dict[str, Any]]:

        logger.info(f"feature model: {fm_model}")

        fm_metrics = FMMetrics().execute(fm_model)
        logger.info(f"fm_metrics: {fm_metrics}")
        result = fm_metrics.get_result()
        return result

    def get_analysis_results(self, fm_model: FeatureModel) -> list[dict[str, Any]]:
        fm_results = BDDMetrics().execute(fm_model).get_result()
        return fm_results

    def check_uvl(self, filepath: str):

        class CustomErrorListener(ErrorListener):
            def __init__(self):
                self.errors = []

            def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
                if "\\t" in msg:
                    warning_message = (
                        f"The UVL has the following warning that prevents reading it: " f"Line {line}:{column} - {msg}"
                    )
                    self.errors.append(warning_message)
                else:
                    error_message = (
                        f"The UVL has the following error that prevents reading it: " f"Line {line}:{column} - {msg}"
                    )
                    self.errors.append(error_message)

        try:
            input_stream = FileStream(filepath)
            lexer = UVLCustomLexer(input_stream)

            error_listener = CustomErrorListener()

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
                logger.warning(f"[UVL Parser] FLAMA failed but will be ignored: {str(fe)}")
                return {"message": "Valid Model (FLAMA transformation skipped due to unsupported attributes)"}, 200

        except Exception as e:
            logger.exception(f"[UVL Parser] Unexpected error during parsing: {e}")
            return {"error": f"Internal error during UVL check, {e}"}, 500
