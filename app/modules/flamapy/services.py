from app.modules.flamapy.repositories import FlamapyRepository
from core.services.BaseService import BaseService
from flamapy.interfaces.python.flamapy_feature_model import FLAMAFeatureModel
from flamapy.core.exceptions import FlamaException

from antlr4 import CommonTokenStream, FileStream
from uvl.UVLCustomLexer import UVLCustomLexer
from uvl.UVLPythonParser import UVLPythonParser
from antlr4.error.ErrorListener import ErrorListener


class FlamapyService(BaseService):
    def __init__(self):
        super().__init__(FlamapyRepository())

    def check_uvl(self, filepath: str):

        class CustomErrorListener(ErrorListener):

            def __init__(self):
                self.errors = []

            def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
                if "\\t" in msg:
                    warning_message = (
                        f"The UVL has the following warning that prevents reading it: "
                        f"Line {line}:{column} - {msg}"
                    )
                    self.errors.append(warning_message)
                else:
                    error_message = (
                        f"The UVL has the following error that prevents reading it: "
                        f"Line {line}:{column} - {msg}"
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
                return {"errors": error_listener.errors}, 400

            try:
                FLAMAFeatureModel(filepath)
                return {"message": "Valid Model"}, 200

            except FlamaException as fe:
                return {"error": f"Model transformation failed: {str(fe)}"}, 400

        except Exception as e:
            return {"error": str(e)}, 500
