import logging
import os

from flask import jsonify, send_file

from app.modules.flamapy import flamapy_bp
from app.modules.hubfile.services import HubfileService

logger = logging.getLogger(__name__)


@flamapy_bp.route("/flamapy/valid/<int:file_id>", methods=["GET"])
def valid(file_id):
    return jsonify({"success": True, "file_id": file_id})


def download_transformed_file(file_id, extension, subdirectory):
    try:
        hubfile = HubfileService().get_or_404(file_id)
        # Obtener el directorio base del dataset, que es el padre de la carpeta 'uvl'
        dataset_dir = os.path.dirname(os.path.dirname(hubfile.get_path()))
        original_filename = os.path.basename(hubfile.get_path())
        transformed_filename = original_filename.replace(".uvl", extension)
        transformed_file_path = os.path.join(dataset_dir, subdirectory, transformed_filename)

        if not os.path.exists(transformed_file_path):
            return (
                jsonify({"error": f"Transformed file not found: {transformed_file_path}"}),
                404,
            )

        return send_file(
            transformed_file_path,
            as_attachment=True,
            download_name=os.path.basename(transformed_file_path),
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flamapy_bp.route("/flamapy/to_glencoe/<int:file_id>", methods=["GET"])
def to_glencoe(file_id):
    return download_transformed_file(file_id, ".json", "glencoe")


@flamapy_bp.route("/flamapy/to_cnf/<int:file_id>", methods=["GET"])
def to_cnf(file_id):
    return download_transformed_file(file_id, ".cnf", "dimacs")


@flamapy_bp.route("/flamapy/to_splot/<int:file_id>", methods=["GET"])
def to_splot(file_id):
    return download_transformed_file(file_id, ".splx", "splot")
