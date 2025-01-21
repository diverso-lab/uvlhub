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
        f"dataset_{hubfile.feature_model.data_set_id}",
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
def view_file(file_id):
    file = HubfileService().get_or_404(file_id)
    filename = file.name

    directory_path = os.path.join(
        "uploads",
        f"user_{file.feature_model.data_set.user_id}",
        f"dataset_{file.feature_model.data_set_id}",
        "uvl",
    )

    parent_directory_path = os.path.dirname(current_app.root_path)
    file_path = os.path.join(parent_directory_path, directory_path, filename)

    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                content = f.read()

            user_cookie = request.cookies.get("view_cookie")
            if not user_cookie:
                user_cookie = str(uuid.uuid4())

            # Check if the view record already exists for this cookie
            existing_record = HubfileViewRecord.query.filter_by(
                user_id=current_user.id if current_user.is_authenticated else None,
                file_id=file_id,
                view_cookie=user_cookie,
            ).first()

            if not existing_record:
                # Register file view
                new_view_record = HubfileViewRecord(
                    user_id=current_user.id if current_user.is_authenticated else None,
                    file_id=file_id,
                    view_date=datetime.now(),
                    view_cookie=user_cookie,
                )
                db.session.add(new_view_record)
                db.session.commit()

                statistics_service = StatisticsService()
                statistics_service.increment_feature_models_viewed()

            # Prepare response
            response = jsonify({"success": True, "content": content})
            if not request.cookies.get("view_cookie"):
                response = make_response(response)
                response.set_cookie(
                    "view_cookie", user_cookie, max_age=60 * 60 * 24 * 365 * 2
                )

            return response
        else:
            return jsonify({"success": False, "error": "File not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
