import logging
from app.modules.hubfile.services import HubfileService
from flask import send_file, jsonify
from app.modules.flamapy import flamapy_bp
from flamapy.interfaces.python.flamapy_feature_model import FLAMAFeatureModel
from flamapy.core.exceptions import FlamaException
import os

from antlr4 import CommonTokenStream, FileStream
from uvl.UVLCustomLexer import UVLCustomLexer
from uvl.UVLPythonParser import UVLPythonParser
from antlr4.error.ErrorListener import ErrorListener

logger = logging.getLogger(__name__)


@flamapy_bp.route('/flamapy/check_uvl/<int:file_id>', methods=['GET'])
def check_uvl(file_id):
    class CustomErrorListener(ErrorListener):
        def __init__(self):
            self.errors = []

        def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
            if "\\t" in msg:
                warning_message = (
                    f"The UVL has the following warning that prevents reading it: "
                    f"Line {line}:{column} - {msg}"
                )
                print(warning_message)
                self.errors.append(warning_message)
            else:
                error_message = (
                    f"The UVL has the following error that prevents reading it: "
                    f"Line {line}:{column} - {msg}"
                )
                self.errors.append(error_message)

    try:
        hubfile = HubfileService().get_by_id(file_id)
        input_stream = FileStream(hubfile.get_path())
        lexer = UVLCustomLexer(input_stream)

        error_listener = CustomErrorListener()

        lexer.removeErrorListeners()
        lexer.addErrorListener(error_listener)

        stream = CommonTokenStream(lexer)
        parser = UVLPythonParser(stream)

        parser.removeErrorListeners()
        parser.addErrorListener(error_listener)

        # Optional: Commented out for now
        # tree = parser.featureModel()

        if error_listener.errors:
            return jsonify({"errors": error_listener.errors}), 400

        # After parsing, try transforming the model
        try:
            # Assuming some logic here like loading and validating the model
            # This part should contain your logic for using the Flamapy transformation
            FLAMAFeatureModel(hubfile.get_path())  # Example usage
            # You can optionally print or process the model here
            return jsonify({"message": "Valid Model"}), 200

        except FlamaException as fe:
            return jsonify({"error": f"Model transformation failed: {str(fe)}"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flamapy_bp.route('/flamapy/valid/<int:file_id>', methods=['GET'])
def valid(file_id):
    return jsonify({"success": True, "file_id": file_id})


def download_transformed_file(file_id, extension, subdirectory):
    try:
        hubfile = HubfileService().get_or_404(file_id)
        # Obtener el directorio base del dataset, que es el padre de la carpeta 'uvl'
        dataset_dir = os.path.dirname(os.path.dirname(hubfile.get_path()))
        original_filename = os.path.basename(hubfile.get_path())
        transformed_filename = original_filename.replace('.uvl', extension)
        transformed_file_path = os.path.join(dataset_dir, subdirectory, transformed_filename)

        if not os.path.exists(transformed_file_path):
            return jsonify({'error': f'Transformed file not found: {transformed_file_path}'}), 404

        return send_file(
            transformed_file_path,
            as_attachment=True,
            download_name=os.path.basename(transformed_file_path)
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@flamapy_bp.route('/flamapy/to_glencoe/<int:file_id>', methods=['GET'])
def to_glencoe(file_id):
    return download_transformed_file(file_id, '.json', 'glencoe')


@flamapy_bp.route('/flamapy/to_cnf/<int:file_id>', methods=['GET'])
def to_cnf(file_id):
    return download_transformed_file(file_id, '.cnf', 'dimacs')


@flamapy_bp.route('/flamapy/to_splot/<int:file_id>', methods=['GET'])
def to_splot(file_id):
    return download_transformed_file(file_id, '.splx', 'splot')
