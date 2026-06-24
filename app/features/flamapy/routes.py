import logging
import os

from flask import jsonify, send_file

from app.features.flamapy import flamapy_bp
from app.features.flamapy.services import FlamapyService

logger = logging.getLogger(__name__)
flamapy_service = FlamapyService()


@flamapy_bp.route("/flamapy/valid/<int:file_id>", methods=["GET"])
def valid(file_id):
    return jsonify({"success": True, "file_id": file_id})


def _send_transformed_file(file_id, extension, subdirectory):
    path = flamapy_service.transformed_file_path(file_id, extension, subdirectory)
    if path is None:
        return jsonify({"error": "Transformed file not found"}), 404
    return send_file(path, as_attachment=True, download_name=os.path.basename(path))


@flamapy_bp.route("/flamapy/to_glencoe/<int:file_id>", methods=["GET"])
def to_glencoe(file_id):
    return _send_transformed_file(file_id, ".json", "glencoe")


@flamapy_bp.route("/flamapy/to_cnf/<int:file_id>", methods=["GET"])
def to_cnf(file_id):
    return _send_transformed_file(file_id, ".cnf", "dimacs")


@flamapy_bp.route("/flamapy/to_splot/<int:file_id>", methods=["GET"])
def to_splot(file_id):
    return _send_transformed_file(file_id, ".splx", "splot")
