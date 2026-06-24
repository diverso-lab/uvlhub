import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from io import BytesIO
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

import qrcode
from flask import (
    abort,
    current_app,
    flash,
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
from PIL import Image, ImageDraw
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from werkzeug.utils import secure_filename

from app.features.apikeys.decorators import require_api_key
from app.features.auth.services import AuthenticationService
from app.features.dataset import dataset_bp, fair_metadata
from app.features.dataset.decorators import is_dataset_owner
from app.features.dataset.forms import DataSetForm
from app.features.dataset.models import DataSet, PublicationType
from app.features.dataset.services import (
    AuthorService,
    DatasetMetadataUpdateError,
    DatasetMetadataValidationError,
    DataSetService,
    DOIMappingService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
    LocalDatasetService,
)
from app.features.elasticsearch.services import IndexingService
from app.features.elasticsearch.utils import index_dataset, index_hubfile
from app.features.featuremodel.services import FeatureModelService
from app.features.hubfile.services import HubfileService
from app.features.zenodo.services import ZenodoDatasetService, ZenodoService

logger = logging.getLogger(__name__)


dataset_service = DataSetService()
author_service = AuthorService()
dsmetadata_service = DSMetaDataService()
zenodo_service = ZenodoService()
doi_mapping_service = DOIMappingService()
ds_view_record_service = DSViewRecordService()
ds_download_record_service = DSDownloadRecordService()
hubfile_service = HubfileService()
authentication_service = AuthenticationService()


def _import_remote_uvl_to_temp(import_url: str, user) -> dict:
    normalized_url = (import_url or "").strip()
    if not normalized_url:
        raise DatasetMetadataValidationError("Missing import URL.")

    parsed_url = urllib_parse.urlparse(normalized_url)
    if parsed_url.scheme not in {"http", "https"}:
        raise DatasetMetadataValidationError("Import URL must use HTTP or HTTPS.")

    original_name = os.path.basename(urllib_parse.unquote(parsed_url.path)) or "imported_model.uvl"
    safe_name = secure_filename(original_name) or "imported_model.uvl"
    if not safe_name.lower().endswith(".uvl"):
        raise DatasetMetadataValidationError("The imported resource must be a .uvl file.")

    request_headers = {"User-Agent": "UVLHub dataset import"}
    remote_request = urllib_request.Request(normalized_url, headers=request_headers)

    try:
        with urllib_request.urlopen(remote_request, timeout=15) as remote_response:
            raw_content = remote_response.read()
    except urllib_error.HTTPError as exc:
        raise DatasetMetadataValidationError(f"Unable to import the remote UVL file (HTTP {exc.code}).") from exc
    except urllib_error.URLError as exc:
        raise DatasetMetadataValidationError("Unable to reach the remote UVL URL.") from exc

    if not raw_content:
        raise DatasetMetadataValidationError("The imported UVL file is empty.")

    try:
        decoded_content = raw_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DatasetMetadataValidationError("The imported UVL file must be UTF-8 encoded.") from exc

    temp_root = user.temp_folder()
    shutil.rmtree(temp_root, ignore_errors=True)
    os.makedirs(temp_root, exist_ok=True)

    import_uuid = str(uuid.uuid4())
    server_filename = f"{import_uuid}_{safe_name}"
    temp_path = os.path.join(temp_root, server_filename)
    with open(temp_path, "w", encoding="utf-8", newline="\n") as imported_file:
        imported_file.write(decoded_content)

    return {
        "name": safe_name,
        "serverFilename": server_filename,
        "size": os.path.getsize(temp_path),
        "uuid": import_uuid,
        "sourceUrl": normalized_url,
    }


@dataset_bp.route("/datasets/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = DataSetForm()

    if request.method == "POST":
        dataset_type = request.form.get("dataset_type", "draft")

        # 1. Create the local dataset
        local_service = LocalDatasetService(
            dsmetadata_service,
            dataset_service,
            author_service,
            FeatureModelService(),
            logger,
        )
        try:
            dataset, ds_meta, created_fms = local_service.create_local_dataset(request.form, current_user)
        except Exception as exc:
            return jsonify({"error": f"Error creating dataset: {str(exc)}"}), 400

        # 2. Draft -> stop here
        if dataset_type == "draft":
            shutil.rmtree(current_user.temp_folder(), ignore_errors=True)
            return (
                jsonify(
                    {
                        "message": "Dataset created locally (draft).",
                        "dataset_id": dataset.id,
                    }
                ),
                200,
            )

        # 3. Zenodo
        if dataset_type in {"zenodo", "zenodo_anonymous"}:
            zenodo_service_facade = ZenodoDatasetService(zenodo_service, dataset_service, logger)
            try:
                doi = zenodo_service_facade.upload_to_zenodo(dataset, ds_meta, dataset_type, current_user)
            except Exception as exc:
                return (
                    jsonify(
                        {
                            "error": (
                                f"Dataset created locally (ID: {dataset.id}), " f"but Zenodo upload failed: {exc}"
                            ),
                            "dataset_id": dataset.id,
                        }
                    ),
                    200,
                )

            # 4. Indexing
            indexing_service = IndexingService(index_dataset, index_hubfile, logger)
            try:
                dataset = dataset_service.get_by_id(dataset.id)  # refreshed after Zenodo
                indexing_service.index_dataset_and_hubfiles(dataset, created_fms)
            except Exception as exc:
                logger.warning(f"[UPLOAD] Dataset {dataset.id} created and uploaded, but indexing failed: {exc}")

            return (
                jsonify(
                    {
                        "message": "Dataset created and uploaded to Zenodo.",
                        "dataset_id": dataset.id,
                        "doi": doi,
                    }
                ),
                200,
            )

        return jsonify({"error": f"Invalid dataset_type: {dataset_type}"}), 400

    hubfile_service.clear_temp()
    return render_template("dataset/create_and_edit_dataset.html", form=form, preloaded_temp_files=[])


@dataset_bp.route("/dataset/import", methods=["GET"])
@dataset_bp.route("/dataset/import/", methods=["GET"])
@login_required
def import_dataset():
    form = DataSetForm()
    import_url = (request.args.get("import") or "").strip()
    preloaded_temp_files = []
    import_error = None
    status_code = 200

    if import_url:
        shutil.rmtree(current_user.temp_folder(), ignore_errors=True)
        os.makedirs(current_user.temp_folder(), exist_ok=True)
        try:
            preloaded_temp_files.append(_import_remote_uvl_to_temp(import_url, current_user))
        except DatasetMetadataValidationError as exc:
            logger.warning("[DATASET IMPORT] Validation error importing %s: %s", import_url, exc)
            import_error = str(exc)
            status_code = 400
        except Exception as exc:
            logger.exception("[DATASET IMPORT] Unexpected error importing %s", import_url)
            import_error = f"Unexpected error importing dataset: {exc}"
            status_code = 400
    else:
        hubfile_service.clear_temp()

    return (
        render_template(
            "dataset/create_and_edit_dataset.html",
            form=form,
            preloaded_temp_files=preloaded_temp_files,
            import_error=import_error,
        ),
        status_code,
    )


@dataset_bp.route("/dataset/edit/<int:dataset_id>", methods=["GET", "POST"])
@login_required
def edit_metadata(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)
    form = DataSetForm()
    if dataset.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        try:
            update_result = dataset_service.update_metadata_from_request(
                dataset,
                request.form,
                zenodo_service=zenodo_service,
            )
            if update_result.get("sync_deferred"):
                warning_message = (
                    "Dataset metadata updated locally. Zenodo is currently unavailable, "
                    "so synchronization is still pending."
                )
                flash(warning_message, "warning")
                if is_ajax:
                    return (
                        jsonify(
                            {
                                "message": warning_message,
                                "metadata_synced": False,
                                "sync_deferred": True,
                            }
                        ),
                        200,
                    )
            if is_ajax:
                return (
                    jsonify(
                        {
                            "message": "Dataset updated successfully",
                            "metadata_synced": update_result.get("metadata_synced", True),
                            "sync_deferred": False,
                        }
                    ),
                    200,
                )
            flash("Dataset updated successfully!", "success")
        except DatasetMetadataValidationError as exc:
            if is_ajax:
                return jsonify({"message": str(exc)}), 400
            flash(str(exc), "danger")
            return redirect(url_for("dataset.edit_metadata", dataset_id=dataset_id))
        except DatasetMetadataUpdateError as exc:
            if is_ajax:
                return jsonify({"message": f"Error updating metadata: {exc}"}), 400
            flash(f"Error updating metadata: {exc}", "danger")
        except Exception as exc:
            logger.exception("[EDIT DATASET] Unexpected error updating dataset %s", dataset_id)
            if is_ajax:
                return jsonify({"message": f"Unexpected error updating metadata: {exc}"}), 400
            flash(f"Unexpected error updating metadata: {exc}", "danger")

        return redirect(url_for("dataset.list_dataset"))

    return render_template(
        "dataset/create_and_edit_dataset.html",
        dataset=dataset,
        is_edit=True,
        form=form,
        PublicationType=PublicationType,
        preloaded_temp_files=[],
    )


@dataset_bp.route("/dataset/<int:dataset_id>/hubfile/<int:hubfile_id>/replace", methods=["POST"])
@login_required
def replace_hubfile(dataset_id, hubfile_id):
    dataset = dataset_service.get_or_404(dataset_id)
    if dataset.user_id != current_user.id:
        abort(403)
    try:
        dataset_service.replace_hubfile(dataset, hubfile_id, request.files.get("file"))
    except (DatasetMetadataValidationError, DatasetMetadataUpdateError) as exc:
        return jsonify({"message": str(exc)}), 400
    return jsonify({"message": "UVL replaced successfully"}), 200


@dataset_bp.route("/dataset/<int:dataset_id>/new-version", methods=["POST"])
@login_required
def new_dataset_version(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)
    if dataset.user_id != current_user.id:
        abort(403)
    try:
        new_dataset = dataset_service.create_new_version(
            dataset, request.files.get("file"), current_user, zenodo_service=zenodo_service
        )
    except (DatasetMetadataValidationError, DatasetMetadataUpdateError) as exc:
        return jsonify({"message": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001 - surface Zenodo/versioning failures to the client
        logger.exception("[NEW VERSION] Unexpected error for dataset %s", dataset_id)
        return jsonify({"message": f"Unexpected error creating the new version: {exc}"}), 400
    return (
        jsonify(
            {
                "message": "New version published to Zenodo.",
                "dataset_id": new_dataset.id,
                "doi": new_dataset.ds_meta_data.dataset_doi,
                "version": new_dataset.dataset_version,
            }
        ),
        200,
    )


_DATASET_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

_ASSET_MIMETYPES = {
    ".js": "text/javascript",
    ".mjs": "text/javascript",
    ".css": "text/css",
}


@dataset_bp.route("/dataset/dist/<path:filename>", methods=["GET"])
def dist_asset(filename):
    """Serve the dataset's compiled front-end assets.

    splent's BaseBlueprint asset route only matches a single path segment and
    reads files in text mode, so it cannot serve the nested TinyMCE runtime
    (models/, themes/, skins/, icons/, plugins/) the description editor loads
    from base_url '/dataset/dist'. This route serves that tree with a path
    converter and binary-safe streaming, taking precedence via its longer prefix.
    """
    response = send_from_directory(os.path.join(_DATASET_ASSETS_DIR, "dist"), filename)
    mimetype = _ASSET_MIMETYPES.get(os.path.splitext(filename)[1])
    if mimetype:
        response.headers["Content-Type"] = mimetype
    return response


@dataset_bp.route("/datasets/list", methods=["GET"])
@login_required
def list_dataset():
    return render_template(
        "dataset/list_datasets.html",
        datasets=dataset_service.get_synchronized_datasets_by_user(current_user.id),
        local_datasets=dataset_service.get_unsynchronized_datasets_by_user(current_user.id),
    )


@dataset_bp.route("/datasets/download/<int:dataset_id>", methods=["GET"])
def download_dataset(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)
    selected_formats = request.args.getlist("formats")
    selected_formats = selected_formats if selected_formats else None

    try:
        zip_path = dataset_service.zip_from_storage(dataset, formats=selected_formats)
    except ValueError as exc:
        abort(400, description=str(exc))

    if not zip_path or not os.path.exists(zip_path):
        abort(404, description="ZIP file not found.")

    user_cookie = ds_download_record_service.create_cookie(dataset)

    resp = make_response(send_file(zip_path, as_attachment=True, mimetype="application/zip"))
    resp.set_cookie("download_cookie", user_cookie)
    return resp


def _build_dataset_qr_response(dataset: DataSet, fmt: str = "png", download: bool = False):
    if not dataset.ds_meta_data.dataset_doi:
        abort(404, description="QR available only for synchronized datasets with DOI.")

    fmt = (fmt or "png").lower()
    if fmt not in {"png", "jpg", "jpeg", "svg"}:
        fmt = "png"

    target_url = url_for("dataset.subdomain_index", doi=dataset.ds_meta_data.dataset_doi, _external=True)

    if fmt == "svg":
        import qrcode.image.svg as qr_svg

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=12,
            border=4,
            image_factory=qr_svg.SvgPathImage,
        )
        qr.add_data(target_url)
        qr.make(fit=True)
        img = qr.make_image()
        img_io = BytesIO()
        img.save(img_io)
        img_io.seek(0)
        return send_file(
            img_io,
            mimetype="image/svg+xml",
            as_attachment=download,
            download_name=f"dataset_{dataset.id}_qr.svg",
        )

    # Raster (PNG / JPG): high resolution, rounded modules, centered logo.
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=24,
        border=4,
    )
    qr.add_data(target_url)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(radius_ratio=0.9),
        fill_color="black",
        back_color="white",
    ).convert("RGBA")

    logo_path = os.path.join(current_app.root_path, "static", "media", "logos", "uvlhub_ball.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        qr_width, qr_height = img.size

        logo_size = max(80, qr_width // 5)
        logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)

        padding = max(8, logo_size // 12)
        logo_background = Image.new(
            "RGBA",
            (logo.width + (2 * padding), logo.height + (2 * padding)),
            (0, 0, 0, 0),
        )
        bg_draw = ImageDraw.Draw(logo_background)
        bg_radius = max(10, logo_background.width // 5)
        bg_draw.rounded_rectangle(
            [(0, 0), (logo_background.width - 1, logo_background.height - 1)],
            radius=bg_radius,
            fill=(255, 255, 255, 255),
        )

        rounded_logo = Image.new("RGBA", logo.size, (0, 0, 0, 0))
        logo_mask = Image.new("L", logo.size, 0)
        logo_mask_draw = ImageDraw.Draw(logo_mask)
        logo_radius = max(6, logo.width // 5)
        logo_mask_draw.rounded_rectangle(
            [(0, 0), (logo.width - 1, logo.height - 1)],
            radius=logo_radius,
            fill=255,
        )
        rounded_logo.paste(logo, (0, 0), logo_mask)

        bg_position = ((qr_width - logo_background.width) // 2, (qr_height - logo_background.height) // 2)
        img.paste(logo_background, bg_position, logo_background)

        logo_position = ((qr_width - rounded_logo.width) // 2, (qr_height - rounded_logo.height) // 2)
        img.paste(rounded_logo, logo_position, rounded_logo)

    img_io = BytesIO()
    if fmt in {"jpg", "jpeg"}:
        flat = Image.new("RGB", img.size, (255, 255, 255))
        flat.paste(img, mask=img.split()[3])  # use alpha channel as mask
        flat.save(img_io, format="JPEG", quality=95, optimize=True)
        mimetype = "image/jpeg"
        ext = "jpg"
    else:
        img.save(img_io, format="PNG", optimize=True)
        mimetype = "image/png"
        ext = "png"
    img_io.seek(0)

    return send_file(
        img_io,
        mimetype=mimetype,
        as_attachment=download,
        download_name=f"dataset_{dataset.id}_qr.{ext}",
    )


def _parse_qr_params():
    return (
        request.args.get("format", "png"),
        request.args.get("download") in {"1", "true", "yes"},
    )


@dataset_bp.route("/datasets/<int:dataset_id>/qr", methods=["GET"])
@dataset_bp.route("/datasets/<int:dataset_id>/qr/", methods=["GET"])
def dataset_qr_by_id(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)
    fmt, download = _parse_qr_params()
    return _build_dataset_qr_response(dataset, fmt=fmt, download=download)


@dataset_bp.route("/doi/<path:doi>/qr", methods=["GET"])
@dataset_bp.route("/doi/<path:doi>/qr/", methods=["GET"])
def dataset_qr_by_doi(doi):
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)
    if not ds_meta_data:
        abort(404, description="Dataset not found for the given DOI.")
    fmt, download = _parse_qr_params()
    return _build_dataset_qr_response(ds_meta_data.dataset, fmt=fmt, download=download)


@dataset_bp.route("/datasets/download/all", methods=["GET"])
def download_all_dataset():
    selected_formats = request.args.getlist("formats")
    selected_formats = selected_formats if selected_formats else None

    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "all_datasets.zip")

    try:
        # Build the ZIP file
        dataset_service.zip_all_datasets_by_formats(zip_path, formats=selected_formats)

        # Build the filename with the current date
        current_date = datetime.now().strftime("%Y_%m_%d")
        zip_filename = f"uvlhub_bulk_{current_date}.zip"

        # Send the file as the response
        return send_file(zip_path, as_attachment=True, download_name=zip_filename)
    except ValueError as exc:
        abort(400, description=str(exc))
    finally:
        # Make sure the temporary folder is removed after Flask serves the file
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


@dataset_bp.route("/doi/<path:doi>", methods=["GET"])
@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):
    # Redirect if the DOI has been superseded
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        return redirect(url_for("dataset.subdomain_index", doi=new_doi), code=302)

    # Look up the dataset by DOI
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)
    if not ds_meta_data:
        abort(404)

    dataset = ds_meta_data.dataset
    host_url = request.host_url
    link_header = fair_metadata.build_link_header(dataset, host_url)

    # Content negotiation: machine clients get structured metadata directly.
    accept = request.accept_mimetypes
    best = accept.best_match(
        [
            "text/html",
            "text/turtle",
            "application/x-turtle",
            "application/rdf+xml",
            "application/ld+json",
            "application/vnd.datacite.datacite+json",
        ],
        default="text/html",
    )

    if best in ("text/turtle", "application/x-turtle", "application/rdf+xml"):
        payload = fair_metadata.build_turtle(dataset, host_url)
        resp = make_response(payload, 200)
        resp.headers["Content-Type"] = "text/turtle; charset=utf-8"
        resp.headers["Link"] = link_header
        resp.headers["Vary"] = "Accept"
        return resp
    if best == "application/ld+json":
        payload = json.dumps(
            fair_metadata.build_json_ld(dataset, host_url),
            indent=2,
            ensure_ascii=False,
        )
        resp = make_response(payload, 200)
        resp.headers["Content-Type"] = "application/ld+json; charset=utf-8"
        resp.headers["Link"] = link_header
        resp.headers["Vary"] = "Accept"
        return resp
    if best == "application/vnd.datacite.datacite+json":
        payload = json.dumps(
            fair_metadata.build_datacite_json(dataset),
            indent=2,
            ensure_ascii=False,
        )
        resp = make_response(payload, 200)
        resp.headers["Content-Type"] = "application/vnd.datacite.datacite+json; charset=utf-8"
        resp.headers["Link"] = link_header
        resp.headers["Vary"] = "Accept"
        return resp

    # HTML fallback (default for browsers and crawlers)
    hubfiles = [file for fm in dataset.feature_models for file in fm.hubfiles]
    selected_file = hubfiles[0] if hubfiles else None

    user_cookie = ds_view_record_service.create_cookie(dataset=dataset)

    meta = dataset.ds_meta_data
    json_ld_payload = json.dumps(
        fair_metadata.build_json_ld(dataset, host_url),
        ensure_ascii=False,
        indent=2,
    ).replace("</", "<\\/")
    fair_meta = {
        "dc_tags": fair_metadata.build_dublin_core_tags(dataset),
        "json_ld_str": json_ld_payload,
        "landing_url": f"{host_url.rstrip('/')}/doi/{meta.dataset_doi or ''}/",
        "doi_url": (f"https://doi.org/{meta.dataset_doi}" if meta.dataset_doi else None),
        "license_url": fair_metadata.CC_BY_40,
        "zenodo_url": (f"https://zenodo.org/record/{meta.deposition_id}" if meta.deposition_id else None),
    }

    resp = make_response(
        render_template(
            "dataset/view_dataset.html",
            dataset=dataset,
            hubfiles=hubfiles,
            selected_file=selected_file,
            uvl_content=None,
            fair_meta=fair_meta,
        )
    )
    resp.set_cookie("view_cookie", user_cookie)
    resp.headers["Link"] = link_header
    resp.headers["Vary"] = "Accept"
    return resp


@dataset_bp.route("/doi/<path:doi>/files/raw/<path:filename>", methods=["GET"])
@dataset_bp.route("/doi/<path:doi>/files/raw/<path:filename>/", methods=["GET"])
def doi_file_raw(doi, filename):

    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        return redirect(
            url_for("dataset.doi_file_raw", doi=new_doi, filename=filename),
            code=302,
        )

    ds_meta_data = dsmetadata_service.filter_by_doi(doi)
    if not ds_meta_data:
        abort(404)

    dataset = ds_meta_data.dataset

    selected_file = None
    for fm in dataset.feature_models:
        for hf in fm.hubfiles:
            if hf.name == filename:
                selected_file = hf
                break
        if selected_file:
            break

    if not selected_file:
        abort(404, description="File not found in this DOI dataset")

    file_path = os.path.join(
        current_app.root_path,
        "..",
        "uploads",
        f"user_{dataset.user_id}",
        f"dataset_{dataset.id}",
        "uvl",
        selected_file.name,
    )

    if not os.path.exists(file_path):
        abort(404, description="File missing on disk")

    return send_file(
        file_path,
        mimetype="text/plain; charset=utf-8",
        as_attachment=False,
        download_name=selected_file.name,
    )


@dataset_bp.route("/datasets/unsynchronized/<int:dataset_id>/", methods=["GET"])
@login_required
@is_dataset_owner
def get_unsynchronized_dataset(dataset_id):
    dataset = dataset_service.get_unsynchronized_dataset_by_user(current_user.id, dataset_id)
    if not dataset:
        abort(404)

    hubfiles = [file for fm in dataset.feature_models for file in fm.hubfiles]
    selected_file = hubfiles[0] if hubfiles else None

    return render_template(
        "dataset/view_dataset.html",
        dataset=dataset,
        hubfiles=hubfiles,
        selected_file=selected_file,
        uvl_content=None,
    )


@dataset_bp.route("/datasets/retry-sync/<int:dataset_id>", methods=["POST"])
@login_required
@is_dataset_owner
def retry_sync_dataset(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)

    if not dataset.ds_meta_data.dataset_doi:
        return jsonify({"error": "Dataset is not synchronized with Zenodo yet"}), 400

    if dataset.ds_meta_data.metadata_synced:
        return jsonify({"error": "Dataset metadata is already in sync"}), 400

    try:
        dataset_service._sync_metadata_in_zenodo_if_needed(dataset, zenodo_service)
        dataset_service.mark_metadata_synced(dataset)
    except Exception as exc:
        logger.exception(f"[RETRY SYNC ERROR] {exc}")
        return jsonify({"error": f"Zenodo sync failed: {exc}"}), 500

    return jsonify({"message": "Metadata successfully synced to Zenodo"}), 200


@dataset_bp.route("/datasets/sync/<int:dataset_id>", methods=["POST", "GET"])
@login_required
@is_dataset_owner
def sync_dataset(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)

    if dataset.ds_meta_data.dataset_doi:
        return jsonify({"error": "Dataset already synchronized"}), 400

    zenodo_service_facade = ZenodoDatasetService(zenodo_service, dataset_service, logger)
    try:
        doi = zenodo_service_facade.upload_to_zenodo(dataset, dataset.ds_meta_data, "zenodo", current_user)
    except Exception as exc:
        logger.exception(f"[SYNC ERROR] {exc}")
        return jsonify({"error": f"Zenodo upload failed: {exc}"}), 400

    # Indexar en Elasticsearch
    indexing_service = IndexingService(index_dataset, index_hubfile, logger)
    try:
        dataset = dataset_service.get_by_id(dataset.id)
        indexing_service.index_dataset_and_hubfiles(dataset, dataset.feature_models)
    except Exception as exc:
        logger.warning(f"[SYNC] Dataset {dataset.id} uploaded, but indexing failed: {exc}")

    if request.method == "GET":
        # Browser redirect
        return redirect(url_for("dataset.list_dataset"))
    else:
        # JSON response (useful for future AJAX callers)
        return jsonify({"message": "Dataset synchronized", "doi": doi}), 200


# REST API


@dataset_bp.route("/api/v1/datasets/upload", methods=["POST"])
def api_upload_dataset():
    """
    Create a draft dataset from a UVL model
    ---
    tags:
      - Datasets
    consumes:
      - multipart/form-data
      - application/json
    parameters:
      - name: title
        in: formData
        type: string
        required: false
        description: Draft dataset title. If omitted, the filename stem is used.
      - name: description
        in: formData
        type: string
        required: false
        description: Optional draft description.
      - name: filename
        in: formData
        type: string
        required: false
        description: Original UVL filename.
      - name: uvl_file
        in: formData
        type: file
        required: false
        description: UVL file to import.
      - name: uvl_content
        in: formData
        type: string
        required: false
        description: Raw UVL content when no file is provided.
    responses:
      201:
        description: Draft dataset created successfully
      400:
        description: Invalid import payload
      401:
        description: Authentication required
    """

    authenticated_user = authentication_service.get_authenticated_user()
    if not authenticated_user:
        payload, status_code = authentication_service.get_flamapy_ide_auth_status_payload()
        return jsonify(payload), status_code

    payload = request.get_json(silent=True) if request.is_json else {}
    uploaded_file = request.files.get("uvl_file") or request.files.get("file")

    title = (payload or {}).get("title") or request.form.get("title")
    description = (payload or {}).get("description") or request.form.get("description") or ""
    filename = (payload or {}).get("filename") or request.form.get("filename")
    uvl_content = (payload or {}).get("uvl_content") or request.form.get("uvl_content")

    if uploaded_file:
        filename = uploaded_file.filename or filename
        try:
            uvl_content = uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError:
            return jsonify({"error": "UVL file must be UTF-8 encoded."}), 400

    if not title:
        inferred_filename = filename or "model.uvl"
        title = os.path.splitext(os.path.basename(inferred_filename))[0].replace("_", " ").strip() or "Imported model"

    try:
        dataset, created_fms = dataset_service.create_draft_from_uvl_import(
            current_user=authenticated_user,
            title=title,
            uvl_content=uvl_content,
            filename=filename,
            description=description,
        )
    except DatasetMetadataValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("[API UPLOAD] Unexpected error importing UVL from flamapyIDE")
        return jsonify({"error": f"Unexpected error creating dataset: {exc}"}), 400

    return (
        jsonify(
            {
                "message": "Dataset draft created successfully.",
                "dataset_id": dataset.id,
                "feature_models_created": len(created_fms),
                "edit_url": url_for("dataset.edit_metadata", dataset_id=dataset.id, _external=True),
                "view_url": url_for("dataset.get_unsynchronized_dataset", dataset_id=dataset.id, _external=True),
                "list_url": url_for("dataset.list_dataset", _external=True),
            }
        ),
        201,
    )


@dataset_bp.route("/api/v1/datasets", methods=["GET"])
@require_api_key("read_dataset")
def api_list_datasets():
    """
    List datasets
    ---
    tags:
      - Datasets
    security:
      - ApiKeyAuth: []
    parameters:
      - name: page
        in: query
        type: integer
        description: Page number
        required: false
        default: 1
    responses:
      200:
        description: Paginated list of datasets
    """

    page = request.args.get("page", 1, type=int)
    per_page = 5

    pagination = dataset_service.paginate(page=page, per_page=per_page)
    items = [ds.to_dict() for ds in pagination.items]

    return jsonify(
        {
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "datasets": items,
        }
    )


@dataset_bp.route("/api/v1/datasets/<int:dataset_id>", methods=["GET"])
@require_api_key("read_dataset")
def api_dataset_detail(dataset_id):
    """
    Get dataset detail
    ---
    tags:
      - Datasets
    security:
      - ApiKeyAuth: []
    parameters:
      - name: dataset_id
        in: path
        type: integer
        required: true
        description: ID of the dataset to retrieve
    responses:
      200:
        description: Dataset details
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: integer
                name:
                  type: string
                description:
                  type: string
                created_at:
                  type: string
                  format: date-time
              example:
                id: 1
                name: "Example Dataset"
                description: "A sample dataset for demonstration purposes."
                created_at: "2025-07-27T10:00:00Z"
      404:
        description: Dataset not found
    """
    dataset = dataset_service.get_by_id(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404
    return jsonify(dataset.to_dict())


@dataset_bp.route("/api/v1/datasets/<int:dataset_id>/summary", methods=["GET"])
@require_api_key("read_dataset")
def api_dataset_summary(dataset_id):
    """
    Get dataset summary
    ---
    tags:
      - Datasets
    security:
      - ApiKeyAuth: []
    parameters:
      - name: dataset_id
        in: path
        type: integer
        required: true
        description: ID of the dataset to summarize
    responses:
      200:
        description: Summary of the dataset
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: integer
                title:
                  type: string
                description:
                  type: string
                publication_type:
                  type: string
                files_count:
                  type: integer
                total_size_in_bytes:
                  type: integer
                total_size_human:
                  type: string
                doi:
                  type: string
                  nullable: true
                created_at:
                  type: string
                  format: date-time
              example:
                id: 2
                title: "My Dataset"
                description: "A dataset summary"
                publication_type: "Journal"
                files_count: 3
                total_size_in_bytes: 1048576
                total_size_human: "1 MB"
                doi: "10.1234/example.doi"
                created_at: "2025-07-27T12:34:56Z"
      404:
        description: Dataset not found
    """
    dataset = dataset_service.get_by_id(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404

    return jsonify(
        {
            "id": dataset.id,
            "title": dataset.name(),
            "description": dataset.description(),
            "publication_type": dataset.get_cleaned_publication_type(),
            "files_count": dataset.get_files_count(),
            "total_size_in_bytes": dataset.get_file_total_size(),
            "total_size_human": dataset.get_file_total_size_for_human(),
            "doi": dataset.ds_meta_data.dataset_doi,
            "created_at": dataset.created_at.isoformat(),
        }
    )


@dataset_bp.route("/api/v1/datasets/<int:dataset_id>/files", methods=["GET"])
@require_api_key("read_dataset")
def api_list_files(dataset_id):
    """
    List files in a dataset
    ---
    tags:
      - Datasets
    security:
      - ApiKeyAuth: []
    parameters:
      - name: dataset_id
        in: path
        type: integer
        required: true
        description: ID of the dataset
      - name: page
        in: query
        type: integer
        required: false
        description: Page number for pagination
        default: 1
    responses:
      200:
        description: Paginated list of files in the dataset
        content:
          application/json:
            schema:
              type: object
              properties:
                page:
                  type: integer
                per_page:
                  type: integer
                total:
                  type: integer
                pages:
                  type: integer
                files:
                  type: array
                  items:
                    type: object
              example:
                page: 1
                per_page: 5
                total: 12
                pages: 3
                files:
                  - id: 101
                    name: "model.uvl"
                    size: 1234
                    checksum: "abcd1234"
                    feature_model_id: 1
                  - id: 102
                    name: "config.uvl"
                    size: 5678
                    checksum: "efgh5678"
                    feature_model_id: 1
      404:
        description: Dataset not found
    """
    dataset = dataset_service.get_by_id(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404

    all_files = dataset.files()
    page = request.args.get("page", 1, type=int)
    per_page = 5

    total = len(all_files)
    start = (page - 1) * per_page
    end = start + per_page
    files_page = all_files[start:end]

    return jsonify(
        {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page,
            "files": [file.to_dict() for file in files_page],
        }
    )


@dataset_bp.route("/api/v1/files/<int:file_id>", methods=["GET"])
@require_api_key("read_dataset")
def api_file_detail(file_id):
    """
    Get file details
    ---
    tags:
      - Files
    security:
      - ApiKeyAuth: []
    parameters:
      - name: file_id
        in: path
        type: integer
        required: true
        description: ID of the file to retrieve
    responses:
      200:
        description: File details
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: integer
                name:
                  type: string
                size:
                  type: integer
                checksum:
                  type: string
                feature_model_id:
                  type: integer
              example:
                id: 42
                name: "example.uvl"
                size: 10240
                checksum: "a1b2c3d4"
                feature_model_id: 7
      404:
        description: File not found
    """
    file = hubfile_service.get_by_id(file_id)
    if not file:
        return jsonify({"error": "File not found"}), 404

    return jsonify(file.to_dict())


@dataset_bp.route("/api/v1/files/<int:file_id>/raw", methods=["GET"])
@require_api_key("read_dataset")
def api_file_raw(file_id):
    """
    Get raw file content
    ---
    tags:
      - Files
    security:
      - ApiKeyAuth: []
    parameters:
      - name: file_id
        in: path
        type: integer
        required: true
        description: ID of the file to retrieve
    responses:
      200:
        description: Raw content of the file
        content:
          text/plain:
            schema:
              type: string
              example: |
                uvl
                root MyFeature
                features
                    MyFeature;
      404:
        description: File not found
      500:
        description: Error reading file from disk
    """
    file = hubfile_service.get_by_id(file_id)
    if not file:
        return jsonify({"error": "File not found"}), 404

    dataset = file.dataset

    file_path = os.path.join(
        current_app.root_path,
        "..",
        "uploads",
        f"user_{dataset.user_id}",
        f"dataset_{dataset.id}",
        "uvl",
        file.name,
    )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content, 200, {"Content-Type": "text/plain; charset=utf-8"}
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dataset_bp.route("/api/v1/files/<int:file_id>/metadata", methods=["GET"])
@require_api_key("read_dataset")
def api_file_metadata(file_id):
    """
    Get metadata of the file's feature model
    ---
    tags:
      - Files
    security:
      - ApiKeyAuth: []
    parameters:
      - name: file_id
        in: path
        type: integer
        required: true
        description: ID of the file whose metadata should be returned
    responses:
      200:
        description: Metadata of the file's feature model
        content:
          application/json:
            schema:
              type: object
              properties:
                title:
                  type: string
                description:
                  type: string
                tags:
                  type: array
                  items:
                    type: string
                publication_type:
                  type: string
                uvl_version:
                  type: string
                publication_doi:
                  type: string
                  nullable: true
                authors:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                      affiliation:
                        type: string
                      orcid:
                        type: string
              example:
                title: "My Feature Model"
                description: "This model represents the configuration options..."
                tags: ["security", "IoT"]
                publication_type: "Conference"
                uvl_version: "1.0"
                publication_doi: "10.5555/example.doi"
                authors:
                  - name: "Alice Smith"
                    affiliation: "University of Sevilla"
                    orcid: "0000-0002-1825-0097"
      404:
        description: File not found or metadata not available
    """
    file = hubfile_service.get_by_id(file_id)
    if not file:
        return jsonify({"error": "File not found"}), 404

    fm = file.feature_model
    if not fm or not fm.fm_meta_data:
        return jsonify({"error": "Metadata not available"}), 404

    meta = fm.fm_meta_data

    return jsonify(
        {
            "title": meta.title,
            "description": meta.description,
            "tags": meta.tags.split(",") if meta.tags else [],
            "publication_type": meta.publication_type.name,
            "uvl_version": meta.uvl_version,
            "publication_doi": meta.publication_doi,
            "authors": [a.to_dict() for a in meta.authors],
        }
    )
