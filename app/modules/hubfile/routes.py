from datetime import datetime
import os
import uuid
from app.modules.flamapy.services import FlamapyService
from flask import current_app, jsonify, make_response, request, send_from_directory
from flask_login import current_user, login_required
from app.modules.hubfile import hubfile_bp
from app.modules.hubfile.models import HubfileViewRecord
from app.modules.hubfile.services import HubfileDownloadRecordService, HubfileService

from app import db
from app.modules.statistics.services import StatisticsService
from flask import render_template

hubfile_download_record_service = HubfileDownloadRecordService()

flamapy_service = FlamapyService()


@hubfile_bp.route("/hubfile/upload", methods=["POST"])
@login_required
def upload_file():
    file = request.files.get("file")
    uuid = request.form.get("uuid")  # Retrieve the UUID sent from the frontend
    temp_folder = current_user.temp_folder()

    if not file or not file.filename.endswith(".uvl"):
        return jsonify({"message": "No valid file"}), 400

    # Validate that the UUID is provided
    if not uuid:
        return jsonify({"message": "UUID is missing"}), 400

    # Safely create the temporary folder
    try:
        os.makedirs(temp_folder, exist_ok=True)  # Handle concurrency safely
    except Exception as e:
        return jsonify({"message": f"Error creating temp folder: {str(e)}"}), 500

    # Generate a unique filename for the file
    unique_filename = f"{uuid}_{file.filename}"

    # Define the temporary path for the file
    temp_file_path = os.path.join(temp_folder, unique_filename)

    # Save the file temporarily
    try:
        file.save(temp_file_path)
    except Exception as e:
        return jsonify({"message": f"Error saving file: {str(e)}"}), 500

    # Validate the UVL file using `check_uvl`
    try:
        validation_result, status_code = flamapy_service.check_uvl(temp_file_path)

        if status_code != 200:
            # If the file is invalid, remove it and return an error
            os.remove(temp_file_path)
            return jsonify(validation_result), status_code

    except Exception as e:
        # Remove the file if an unexpected error occurs during validation
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return jsonify({"message": f"Error validating UVL: {str(e)}"}), 500

    # If the file is valid, return the unique filename
    return (
        jsonify(
            {
                "message": "UVL uploaded and validated successfully",
                "filename": unique_filename,
            }
        ),
        200,
    )


@hubfile_bp.route("/hubfile/delete", methods=["POST"])
@login_required
def delete():
    data = request.get_json()
    filename = data.get("filename")  # Nombre original del archivo
    uuid = data.get("uuid")  # UUID enviado desde el frontend
    temp_folder = current_user.temp_folder()

    # Generar el nombre único del archivo
    unique_filename = f"{uuid}_{filename}"
    filepath = os.path.join(temp_folder, unique_filename)

    # Verificar si el archivo existe y eliminarlo
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": "File deleted successfully"}), 200

    return jsonify({"error": "Error: File not found"}), 404


@hubfile_bp.route("/hubfile/download/<int:file_id>", methods=["GET"])
def download_file(file_id):
    hubfile = HubfileService().get_or_404(file_id)
    user_owner = hubfile.get_owner_user()
    filename = hubfile.name

    directory_path = os.path.join(
        "uploads",
        f"user_{user_owner.id}",
        f"dataset_{hubfile.feature_model.dataset_id}",
        "uvl",
    )

    parent_directory_path = os.path.dirname(current_app.root_path)
    file_path = os.path.join(parent_directory_path, directory_path)

    user_cookie = hubfile_download_record_service.create_cookie(hubfile=hubfile)

    resp = make_response(
        send_from_directory(directory=file_path, path=filename, as_attachment=True)
    )
    resp.set_cookie("file_download_cookie", user_cookie)

    return resp


@hubfile_bp.route("/hubfile/view/<int:file_id>", methods=["GET"])
def view_uvl(file_id):
    selected_file = HubfileService().get_or_404(file_id)
    dataset = selected_file.feature_model.data_set

    # Leer contenido UVL
    directory_path = os.path.join(
        "uploads",
        f"user_{dataset.user_id}",
        f"dataset_{dataset.id}",
        "uvl"
    )
    file_path = os.path.join(current_app.root_path, "..", directory_path, selected_file.name)

    try:
        with open(file_path, "r") as f:
            content = f.read()
    except Exception as e:
        content = f"[Error reading file: {e}]"

    return render_template(
        "hubfile/view_file.html",
        selected_file=selected_file,
        hubfiles=dataset.files(),
        dataset=dataset,
        uvl_content=content
    )


@hubfile_bp.route("/hubfile/raw/<int:file_id>", methods=["GET"])
def raw_uvl(file_id):
    selected_file = HubfileService().get_or_404(file_id)
    dataset = selected_file.feature_model.data_set

    # Construir ruta absoluta al archivo
    directory_path = os.path.join(
        "uploads",
        f"user_{dataset.user_id}",
        f"dataset_{dataset.id}",
        "uvl"
    )
    file_path = os.path.join(current_app.root_path, "..", directory_path, selected_file.name)

    try:
        with open(file_path, "r") as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
