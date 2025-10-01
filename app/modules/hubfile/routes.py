import os

from flask import (
    abort,
    current_app,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required

from app.modules.dataset.decorators import is_dataset_owner
from app.modules.dataset.services import DataSetService, DOIMappingService, DSMetaDataService
from app.modules.flamapy.services import FlamapyService
from app.modules.hubfile import hubfile_bp
from app.modules.hubfile.services import HubfileDownloadRecordService, HubfileService

hubfile_download_record_service = HubfileDownloadRecordService()

flamapy_service = FlamapyService()
doi_mapping_service = DOIMappingService()
dsmetadata_service = DSMetaDataService()
hubfile_service = HubfileService()
dataset_service = DataSetService()


@hubfile_bp.route("/hubfile/upload", methods=["POST"])
@login_required
def upload_file():
    current_app.logger.info("➡️ Entrando en /hubfile/upload")

    file = request.files.get("file")
    uuid = request.form.get("uuid")  # Retrieve the UUID sent from the frontend
    temp_folder = current_user.temp_folder()

    current_app.logger.info(f"📂 temp_folder={temp_folder}, uuid={uuid}, file={file.filename if file else None}")

    if not file:
        current_app.logger.warning("⚠️ No file uploaded")
        return jsonify({"message": "No file uploaded"}), 400

    if not uuid:
        current_app.logger.warning("⚠️ UUID is missing")
        return jsonify({"message": "UUID is missing"}), 400

    # Crear carpeta temporal
    try:
        os.makedirs(temp_folder, exist_ok=True)
        current_app.logger.info(f"📁 Carpeta temporal asegurada: {temp_folder}")
    except Exception as e:
        current_app.logger.exception("❌ Error creando carpeta temporal")
        return jsonify({"message": f"Error creating temp folder: {str(e)}"}), 500

    # Nombre único y path
    unique_filename = f"{uuid}_{file.filename}"
    temp_file_path = os.path.join(temp_folder, unique_filename)
    current_app.logger.info(f"📝 unique_filename={unique_filename}, temp_file_path={temp_file_path}")

    # Guardar archivo temporalmente
    try:
        file.save(temp_file_path)
        current_app.logger.info(f"✅ Archivo guardado en {temp_file_path}")
    except Exception as e:
        current_app.logger.exception("❌ Error guardando archivo")
        return jsonify({"message": f"Error saving file: {str(e)}"}), 500

    ext = file.filename.lower().split(".")[-1]
    current_app.logger.info(f"📦 Detected extension: {ext}")

    if ext == "uvl":
        try:
            current_app.logger.info("⚙️ Encolando validación UVL async...")
            task_info = flamapy_service.check_uvl_async(temp_file_path)
            current_app.logger.info(f"✅ Tarea encolada correctamente: {task_info}")
            return (
                jsonify(
                    {
                        "message": f"{ext.upper()} uploaded successfully (validation running in background)",
                        "filename": unique_filename,
                        "task_id": task_info["task_id"],
                    }
                ),
                202,
            )
        except Exception as e:
            current_app.logger.exception("❌ Error encolando validación UVL")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                current_app.logger.info(f"🗑️ Archivo temporal eliminado tras fallo: {temp_file_path}")
            return jsonify({"message": f"Error encolando validación UVL: {str(e)}"}), 500

    elif ext == "zip":
        current_app.logger.info("📦 ZIP detectado → no se valida, solo se acepta")
        # Do not validate ZIPs, just accept them
        pass
    else:
        current_app.logger.warning(f"⚠️ Extensión no soportada: {ext}")
        os.remove(temp_file_path)
        current_app.logger.info(f"🗑️ Archivo eliminado: {temp_file_path}")
        return jsonify({"message": "Unsupported file type"}), 400

    current_app.logger.info(f"✅ Archivo {unique_filename} aceptado con extensión {ext}")
    return (
        jsonify(
            {
                "message": f"{ext.upper()} uploaded successfully",
                "filename": unique_filename,
            }
        ),
        200,
    )


@hubfile_bp.route("/hubfile/delete", methods=["POST"])
@login_required
def delete():
    data = request.get_json()
    filename = data.get("filename")
    temp_folder = current_user.temp_folder()

    if not filename:
        return jsonify({"message": "Filename is missing"}), 400

    file_path = os.path.join(temp_folder, filename)

    if not os.path.exists(file_path):
        return jsonify({"message": "File not found"}), 404

    try:
        os.remove(file_path)
        return jsonify({"message": "File deleted successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Error deleting file: {str(e)}"}), 500


@hubfile_bp.route("/hubfiles/download/<int:file_id>", methods=["GET"])
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

    resp = make_response(send_from_directory(directory=file_path, path=filename, as_attachment=True))
    resp.set_cookie("file_download_cookie", user_cookie)

    return resp


@hubfile_bp.route("/hubfile/clear_temp", methods=["POST"])
@login_required
def clear_temp():
    return hubfile_service.clear_temp()


@hubfile_bp.route("/datasets/unsynchronized/<int:dataset_id>/files/<int:file_id>")
@login_required
@is_dataset_owner
def view_unsynchronized_file(dataset_id, file_id):
    # Buscar dataset y archivo en base de datos
    dataset = dataset_service.get_by_id(dataset_id)
    selected_file = hubfile_service.get_by_id(file_id)

    if not dataset or not selected_file:
        abort(404)

    # 4. Construir ruta al archivo en disco
    directory_path = os.path.join("uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}", "uvl")
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
        uvl_content=content,
    )


@hubfile_bp.route("/doi/<path:doi>/files/<string:filename>", methods=["GET"])
def view_uvl_with_doi(doi, filename):
    # 1. Comprobar si el DOI está redirigido a otro
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        return redirect(
            url_for("hubfile.view_uvl_with_doi", doi=new_doi, filename=filename),
            code=302,
        )

    # 2. Buscar dataset por DOI
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)
    if not ds_meta_data:
        abort(404)

    dataset = ds_meta_data.dataset

    # 3. Buscar hubfile por nombre dentro del dataset
    selected_file = next(
        (hf for fm in dataset.feature_models for hf in fm.hubfiles if hf.name == filename),
        None,
    )
    if not selected_file:
        abort(404)

    # 4. Construir ruta al archivo en disco
    directory_path = os.path.join("uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}", "uvl")
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
        uvl_content=content,
    )


@hubfile_bp.route("/hubfiles/raw/<int:file_id>/<path:filename>", methods=["GET"])
def raw_uvl(file_id, filename):
    selected_file = HubfileService().get_or_404(file_id)
    dataset = selected_file.feature_model.dataset

    directory_path = os.path.join("uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}", "uvl")
    file_path = os.path.join(current_app.root_path, "..", directory_path, selected_file.name)

    # Seguridad: comprobar que coincide
    if filename != selected_file.name:
        return jsonify({"error": "Filename mismatch"}), 400

    return send_file(
        file_path, mimetype="text/plain; charset=utf-8", as_attachment=False, download_name=selected_file.name
    )
