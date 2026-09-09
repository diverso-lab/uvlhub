import os
import uuid as uuid_module
from io import BytesIO

import requests
from flask import (
    abort,
    current_app,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required

from app.features.dataset.decorators import is_dataset_owner
from app.features.dataset.services import DataSetService, DOIMappingService, DSMetaDataService
from app.features.hubfile import hubfile_bp
from app.features.hubfile.services import (
    HubfileDownloadRecordService,
    HubfileService,
    HubfileViewRecordService,
)

hubfile_view_record_service = HubfileViewRecordService()
hubfile_download_record_service = HubfileDownloadRecordService()

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


@hubfile_bp.route("/hubfile/upload-github", methods=["POST"])
@login_required
def upload_from_github():
    """Download a UVL file from GitHub and save it to temp folder"""
    current_app.logger.info("Entering /hubfile/upload-github")

    try:
        data = request.get_json()
        github_url = data.get("github_url", "").strip()
        branch = data.get("branch", "main").strip()
        file_path = data.get("file_path", "").strip()

        current_app.logger.info(f"github_url={github_url}, branch={branch}, file_path={file_path}")

        # Validar parámetros
        if not github_url:
            current_app.logger.warning("GitHub URL is missing")
            return jsonify({"message": "GitHub URL is required"}), 400

        if not file_path:
            current_app.logger.warning("File path is missing")
            return jsonify({"message": "File path is required"}), 400

        # Validar que sea GitHub
        if "github.com" not in github_url.lower():
            current_app.logger.warning(f"Invalid GitHub URL: {github_url}")
            return jsonify({"message": "Invalid GitHub URL. Must be from github.com"}), 400

        # Limpiar URL (remover .git, https://, github.com/, etc)
        github_url = github_url.rstrip("/").replace(".git", "")
        if github_url.startswith("https://"):
            github_url = github_url[8:]
        elif github_url.startswith("http://"):
            github_url = github_url[7:]

        # Remove github.com/ prefix
        if github_url.startswith("github.com/"):
            github_url = github_url[11:]

        # Construir URL raw de GitHub
        # Formato: https://raw.githubusercontent.com/owner/repo/branch/path/file.uvl
        raw_url = f"https://raw.githubusercontent.com/{github_url}/{branch}/{file_path}"
        current_app.logger.info(f"Downloading from: {raw_url}")

        # Descargar archivo
        try:
            response = requests.get(raw_url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            current_app.logger.warning("GitHub download timeout")
            return jsonify({"message": "GitHub download timeout. File is too large or connection is slow"}), 408
        except requests.exceptions.HTTPError as e:
            current_app.logger.warning(f"GitHub HTTP error: {e.response.status_code}")
            if e.response.status_code == 404:
                return jsonify({"message": "File not found on GitHub. Check repository, branch, and path"}), 404
            return jsonify({"message": f"GitHub error: {e.response.status_code}"}), 400
        except requests.exceptions.RequestException as e:
            current_app.logger.exception(f"Error downloading from GitHub: {e}")
            return jsonify({"message": f"Error downloading from GitHub: {str(e)}"}), 500

        # Validar que sea archivo .uvl
        filename = file_path.split("/")[-1]
        if not filename.lower().endswith(".uvl"):
            current_app.logger.warning(f"Invalid file extension: {filename}")
            return jsonify({"message": "File must be a .uvl file"}), 400

        # Validar tamaño (100 MB)
        max_size = 100 * 1024 * 1024
        if len(response.content) > max_size:
            current_app.logger.warning(f"File too large: {len(response.content)} bytes")
            return jsonify({"message": "File too large. Maximum size is 100 MB"}), 413

        # Obtener temp folder del usuario
        temp_folder = current_user.temp_folder()

        # Crear carpeta temporal
        try:
            os.makedirs(temp_folder, exist_ok=True)
            current_app.logger.info(f"Temporary folder ready: {temp_folder}")
        except Exception as e:
            current_app.logger.exception("Error creating temporary folder")
            return jsonify({"message": f"Error creating temp folder: {str(e)}"}), 500

        # Generar nombre único
        unique_id = str(uuid_module.uuid4())
        unique_filename = f"{unique_id}_{filename}"
        temp_file_path = os.path.join(temp_folder, unique_filename)
        current_app.logger.info(f"unique_filename={unique_filename}, temp_file_path={temp_file_path}")

        # Guardar archivo
        try:
            with open(temp_file_path, "wb") as f:
                f.write(response.content)
            current_app.logger.info(f"File saved at {temp_file_path}")
        except Exception as e:
            current_app.logger.exception("Error saving file")
            return jsonify({"message": f"Error saving file: {str(e)}"}), 500

        # Retornar éxito
        current_app.logger.info(f"File {unique_filename} accepted from GitHub")
        return (
            jsonify(
                {
                    "message": "UVL uploaded successfully from GitHub",
                    "filename": unique_filename,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.exception(f"Unexpected error in upload_from_github: {e}")
        return jsonify({"message": f"Unexpected error: {str(e)}"}), 500


@hubfile_bp.route("/hubfile/list-github-files", methods=["POST"])
@login_required
def list_github_files():
    """List all .uvl files in a GitHub folder"""
    current_app.logger.info("Entering /hubfile/list-github-files")

    try:
        data = request.get_json()
        github_url = data.get("github_url", "").strip()
        branch = data.get("branch", "main").strip()
        folder_path = data.get("folder_path", "").strip()

        current_app.logger.info(f"github_url={github_url}, branch={branch}, folder_path={folder_path}")

        # Validar parámetros
        if not github_url:
            return jsonify({"message": "GitHub URL is required"}), 400

        if not folder_path:
            return jsonify({"message": "Folder path is required"}), 400

        # Validar que sea GitHub
        if "github.com" not in github_url.lower():
            return jsonify({"message": "Invalid GitHub URL. Must be from github.com"}), 400

        # Limpiar URL
        github_url = github_url.rstrip("/").replace(".git", "")
        if github_url.startswith("https://"):
            github_url = github_url[8:]
        elif github_url.startswith("http://"):
            github_url = github_url[7:]

        if github_url.startswith("github.com/"):
            github_url = github_url[11:]

        # Normalizar folder path (remover .git, etc)
        folder_path = folder_path.rstrip("/")

        # Usar GitHub API para listar archivos
        # Formato: https://api.github.com/repos/owner/repo/contents/folder
        api_url = f"https://api.github.com/repos/{github_url}/contents/{folder_path}"

        current_app.logger.info(f"Fetching from API: {api_url}")

        try:
            response = requests.get(api_url, params={"ref": branch}, timeout=10)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            return jsonify({"message": "GitHub API timeout"}), 408
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"message": "Folder not found on GitHub"}), 404
            return jsonify({"message": f"GitHub API error: {e.response.status_code}"}), 400
        except requests.exceptions.RequestException as e:
            current_app.logger.exception(f"Error fetching from GitHub API: {e}")
            return jsonify({"message": f"Error connecting to GitHub API: {str(e)}"}), 500

        # Procesar respuesta
        contents = response.json()

        # Si no es una lista, significa que es un archivo único
        if not isinstance(contents, list):
            return jsonify({"message": "Path is not a folder"}), 400

        # Filtrar solo archivos .uvl
        uvl_files = [
            item["name"] for item in contents if item["type"] == "file" and item["name"].lower().endswith(".uvl")
        ]

        if not uvl_files:
            return jsonify({"message": "No .uvl files found in this folder"}), 404

        current_app.logger.info(f"Found {len(uvl_files)} .uvl files")

        return jsonify({"files": uvl_files}), 200

    except Exception as e:
        current_app.logger.exception(f"Unexpected error in list_github_files: {e}")
        return jsonify({"message": f"Unexpected error: {str(e)}"}), 500


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

    file_path = hubfile.get_full_path()

    user_cookie = hubfile_download_record_service.create_cookie(hubfile=hubfile)

    resp = make_response(send_file(file_path, as_attachment=True, download_name=hubfile.name))
    resp.set_cookie("file_download_cookie", user_cookie)

    return resp


@hubfile_bp.route("/hubfile/clear_temp", methods=["POST"])
@login_required
def clear_temp():
    try:
        hubfile_service.clear_temp()
        return jsonify({"message": "Temp folder cleared"}), 200
    except Exception as e:
        return jsonify({"error": f"Error clearing temp folder: {str(e)}"}), 500


@hubfile_bp.route("/datasets/unsynchronized/<int:dataset_id>/files/<int:file_id>")
@login_required
@is_dataset_owner
def view_unsynchronized_file(dataset_id, file_id):
    # Look up dataset and file in the database.
    dataset = dataset_service.get_by_id(dataset_id)
    selected_file = hubfile_service.get_by_id(file_id)

    if not dataset or not selected_file:
        abort(404)

    user_cookie = hubfile_view_record_service.create_cookie(hubfile=selected_file)
    resp = make_response(
        render_template(
            "dataset/view_dataset.html",
            selected_file=selected_file,
            hubfiles=dataset.files(),
            dataset=dataset,
            uvl_content=None,
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
        (hf for fm in dataset.feature_models for hf in fm.hubfiles if filename in (hf.name, hf.relative_path)),
        None,
    )
    if not selected_file:
        abort(404)

    user_cookie = hubfile_view_record_service.create_cookie(hubfile=selected_file)
    resp = make_response(
        render_template(
            "dataset/view_dataset.html",
            selected_file=selected_file,
            hubfiles=dataset.files(),
            dataset=dataset,
            uvl_content=None,
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
    selected_file.dataset

    file_path = selected_file.get_full_path()

    # Security: check that the name matches.
    if filename != selected_file.name:
        return jsonify({"error": "Filename mismatch"}), 400

    # Let send_file add the charset once — passing "text/plain; charset=utf-8"
    # as mimetype makes Flask append another "; charset=utf-8", resulting in
    # a duplicated parameter that some CORS-capable fetchers (notably the
    # FactLabel web app) choke on.
    return send_file(file_path, mimetype="text/plain", as_attachment=False, download_name=selected_file.name)


@hubfile_bp.route("/hubfiles/<int:file_id>/workbench-content", methods=["GET"])
def workbench_content(file_id):
    """Return the UVL + FactLabel JSON for a single file.

    Access mirrors the HTML routes:
      - If the parent dataset has a DOI, the content is public.
      - Otherwise only the owner (authenticated) may read it.
    """
    import json as _json

    selected_file = HubfileService().get_or_404(file_id)
    dataset = selected_file.dataset

    is_public = bool(dataset.ds_meta_data and dataset.ds_meta_data.dataset_doi)
    if not is_public:
        if not current_user.is_authenticated or dataset.user_id != current_user.id:
            abort(403)

    file_path = selected_file.get_full_path()
    try:
        with open(file_path, "r") as f:
            uvl = f.read()
    except Exception as e:
        uvl = f"[Error reading file: {e}]"

    factlabel = None
    if selected_file.factlabel and selected_file.factlabel.factlabel_json:
        try:
            factlabel = _json.loads(selected_file.factlabel.factlabel_json)
        except Exception:
            factlabel = None

    user_cookie = hubfile_view_record_service.create_cookie(hubfile=selected_file)
    # The UVL-tool URLs are provided by the domain features as template globals;
    # the generic hub reads them without importing flamapy/factlabel.
    ide_url_fn = current_app.jinja_env.globals.get("ide_url")
    factlabel_url_fn = current_app.jinja_env.globals.get("factlabel_url")
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
                "ide_url": ide_url_fn(selected_file) if ide_url_fn else None,
                "factlabel_external_url": factlabel_url_fn(selected_file) if factlabel_url_fn else None,
                "view_url": selected_file.get_url(),
            }
        )
    )
    resp.set_cookie("file_view_cookie", user_cookie)
    return resp


def _generate_latex_content(file_id, include_document=False):
    """Helper function to generate LaTeX content from UVL file."""
    selected_file = HubfileService().get_or_404(file_id)
    selected_file.dataset

    file_path = selected_file.get_full_path()

    try:
        with open(file_path, "r") as f:
            uvl_content = f.read()
    except Exception as e:
        current_app.logger.error(f"Error reading UVL file {file_id}: {e}")
        return None

    latex_content = r"\usepackage{uvlhighlight}" + "\n\n"

    if include_document:
        latex_content += r"\begin{document}" + "\n\n"

    latex_content += r"\begin{lstlisting}[language=UVL]" + "\n"
    latex_content += uvl_content
    if not uvl_content.endswith("\n"):
        latex_content += "\n"
    latex_content += r"\end{lstlisting}" + "\n"

    if include_document:
        latex_content += "\n" + r"\end{document}" + "\n"

    return latex_content


@hubfile_bp.route("/hubfile/to_latex/<int:file_id>", methods=["GET"])
def to_latex_content(file_id):
    """Get LaTeX content as JSON (for displaying in modal)."""
    latex_content = _generate_latex_content(file_id, include_document=False)
    if latex_content is None:
        return jsonify({"error": "Could not read file"}), 500

    selected_file = HubfileService().get_or_404(file_id)
    tex_filename = selected_file.name.replace(".uvl", ".tex")

    return jsonify({"content": latex_content, "filename": tex_filename}), 200


@hubfile_bp.route("/hubfile/to_latex_zip/<int:file_id>", methods=["GET"])
def to_latex_zip(file_id):
    """Export UVL to LaTeX + package files as ZIP."""
    import zipfile
    from pathlib import Path

    selected_file = HubfileService().get_or_404(file_id)
    latex_content = _generate_latex_content(file_id, include_document=False)
    if latex_content is None:
        return jsonify({"error": "Could not read file"}), 500

    tex_filename = selected_file.name.replace(".uvl", ".tex")

    # Crear ZIP con el .tex + archivos del paquete
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Agregar el archivo .tex
        zip_file.writestr(tex_filename, latex_content)

        # Agregar archivos del paquete uvlhighlight
        package_path = Path(current_app.root_path) / "static" / "uvlhighlight"
        if package_path.exists():
            for file in package_path.rglob("*"):
                if file.is_file():
                    arcname = file.relative_to(package_path.parent)
                    zip_file.writestr(str(arcname), file.read_bytes())

    zip_buffer.seek(0)
    zip_filename = selected_file.name.replace(".uvl", ".zip")

    return send_file(zip_buffer, as_attachment=True, download_name=zip_filename, mimetype="application/zip")
