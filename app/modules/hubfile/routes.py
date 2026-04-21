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
from app.modules.hubfile.services import (
    HubfileDownloadRecordService,
    HubfileService,
    HubfileViewRecordService,
)

hubfile_view_record_service = HubfileViewRecordService()
hubfile_download_record_service = HubfileDownloadRecordService()

flamapy_service = FlamapyService()
doi_mapping_service = DOIMappingService()
dsmetadata_service = DSMetaDataService()
hubfile_service = HubfileService()
dataset_service = DataSetService()


@hubfile_bp.route("/hubfile/upload", methods=["POST"])
@login_required
def upload_file():
    current_app.logger.info("Entering /hubfile/upload")

    file = request.files.get("file")
    uuid = request.form.get("uuid")  # Retrieve the UUID sent from the frontend
    temp_folder = current_user.temp_folder()

    current_app.logger.info(f"temp_folder={temp_folder}, uuid={uuid}, file={file.filename if file else None}")

    if not file:
        current_app.logger.warning("No file uploaded")
        return jsonify({"message": "No file uploaded"}), 400

    if not uuid:
        current_app.logger.warning("UUID is missing")
        return jsonify({"message": "UUID is missing"}), 400

    # Create temporary folder
    try:
        os.makedirs(temp_folder, exist_ok=True)
        current_app.logger.info(f"Temporary folder ready: {temp_folder}")
    except Exception as e:
        current_app.logger.exception("Error creating temporary folder")
        return jsonify({"message": f"Error creating temp folder: {str(e)}"}), 500

    # Unique name and path
    unique_filename = f"{uuid}_{file.filename}"
    temp_file_path = os.path.join(temp_folder, unique_filename)
    current_app.logger.info(f"unique_filename={unique_filename}, temp_file_path={temp_file_path}")

    # Save file temporarily
    try:
        file.save(temp_file_path)
        current_app.logger.info(f"File saved at {temp_file_path}")
    except Exception as e:
        current_app.logger.exception("Error saving file")
        return jsonify({"message": f"Error saving file: {str(e)}"}), 500

    ext = file.filename.lower().split(".")[-1]
    current_app.logger.info(f"Detected extension: {ext}")

    current_app.logger.info(f"File {unique_filename} accepted with extension {ext}")
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
    # Look up dataset and file in the database.
    dataset = dataset_service.get_by_id(dataset_id)
    selected_file = hubfile_service.get_by_id(file_id)

    if not dataset or not selected_file:
        abort(404)

    # 4. Build the on-disk path to the file.
    directory_path = os.path.join("uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}", "uvl")
    file_path = os.path.join(current_app.root_path, "..", directory_path, selected_file.name)

    try:
        with open(file_path, "r") as f:
            content = f.read()
    except Exception as e:
        content = f"[Error reading file: {e}]"

    user_cookie = hubfile_view_record_service.create_cookie(hubfile=selected_file)
    resp = make_response(
        render_template(
            "dataset/view_dataset.html",
            selected_file=selected_file,
            hubfiles=dataset.files(),
            dataset=dataset,
            uvl_content=content,
        )
    )
    resp.set_cookie("file_view_cookie", user_cookie)
    return resp


@hubfile_bp.route("/doi/<path:doi>/files/<string:filename>", methods=["GET"])
def view_uvl_with_doi(doi, filename):
    # 1. Check whether the DOI has been redirected to another one.
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        return redirect(
            url_for("hubfile.view_uvl_with_doi", doi=new_doi, filename=filename),
            code=302,
        )

    # 2. Look up the dataset by DOI.
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)
    if not ds_meta_data:
        abort(404)

    dataset = ds_meta_data.dataset

    # 3. Find the hubfile by name within the dataset.
    selected_file = next(
        (hf for fm in dataset.feature_models for hf in fm.hubfiles if hf.name == filename),
        None,
    )
    if not selected_file:
        abort(404)

    # 4. Build the on-disk path to the file.
    directory_path = os.path.join("uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}", "uvl")
    file_path = os.path.join(current_app.root_path, "..", directory_path, selected_file.name)

    try:
        with open(file_path, "r") as f:
            content = f.read()
    except Exception as e:
        content = f"[Error reading file: {e}]"

    user_cookie = hubfile_view_record_service.create_cookie(hubfile=selected_file)
    resp = make_response(
        render_template(
            "dataset/view_dataset.html",
            selected_file=selected_file,
            hubfiles=dataset.files(),
            dataset=dataset,
            uvl_content=content,
        )
    )
    resp.set_cookie("file_view_cookie", user_cookie)
    return resp


@hubfile_bp.route("/hubfiles/raw/<int:file_id>/<path:filename>", methods=["GET"])
def raw_uvl(file_id, filename):
    # CORS is configured at app factory level via flask_cors
    # ({"/hubfiles/raw/*": {"origins": "*"}}), which is what lets
    # fmfactlabel.github.io and ide.flamapy.org fetch this endpoint
    # cross-origin — same behaviour as GitHub's raw URLs.
    selected_file = HubfileService().get_or_404(file_id)
    dataset = selected_file.feature_model.dataset

    directory_path = os.path.join("uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}", "uvl")
    file_path = os.path.join(current_app.root_path, "..", directory_path, selected_file.name)

    # Security: check that the name matches.
    if filename != selected_file.name:
        return jsonify({"error": "Filename mismatch"}), 400

    # Let send_file add the charset once — passing "text/plain; charset=utf-8"
    # as mimetype makes Flask append another "; charset=utf-8", resulting in
    # a duplicated parameter that some CORS-capable fetchers (notably the
    # FactLabel web app) choke on.
    return send_file(
        file_path, mimetype="text/plain", as_attachment=False, download_name=selected_file.name
    )


@hubfile_bp.route("/hubfiles/<int:file_id>/workbench-content", methods=["GET"])
def workbench_content(file_id):
    """Return the UVL + FactLabel JSON for a single file.

    Access mirrors the HTML routes:
      - If the parent dataset has a DOI, the content is public.
      - Otherwise only the owner (authenticated) may read it.
    """
    import json as _json

    selected_file = HubfileService().get_or_404(file_id)
    dataset = selected_file.feature_model.dataset

    is_public = bool(dataset.ds_meta_data and dataset.ds_meta_data.dataset_doi)
    if not is_public:
        if not current_user.is_authenticated or dataset.user_id != current_user.id:
            abort(403)

    directory_path = os.path.join("uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}", "uvl")
    file_path = os.path.join(current_app.root_path, "..", directory_path, selected_file.name)
    try:
        with open(file_path, "r") as f:
            uvl = f.read()
    except Exception as e:
        uvl = f"[Error reading file: {e}]"

    factlabel = None
    if selected_file.factlabel_json:
        try:
            factlabel = _json.loads(selected_file.factlabel_json)
        except Exception:
            factlabel = None

    user_cookie = hubfile_view_record_service.create_cookie(hubfile=selected_file)
    resp = make_response(
        jsonify(
            {
                "id": selected_file.id,
                "name": selected_file.name,
                "size_bytes": selected_file.size,
                "size_human": selected_file.get_formatted_size(),
                "uvl": uvl,
                "factlabel": factlabel,
                "factlabel_ready": factlabel is not None,
                "download_url": url_for("hubfile.download_file", file_id=selected_file.id),
                "raw_url": url_for("hubfile.raw_uvl", file_id=selected_file.id, filename=selected_file.name),
                "ide_url": selected_file.get_ide_url(),
                "factlabel_external_url": selected_file.get_factlabel_url(),
                "view_url": selected_file.get_url(),
            }
        )
    )
    resp.set_cookie("file_view_cookie", user_cookie)
    return resp
