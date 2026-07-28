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
    g,
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

from app.features.apikeys.decorators import require_api_key, resolve_api_key
from app.features.auth.services import AuthenticationService
from app.features.dataset import dataset_bp, fair_metadata
from app.features.dataset.decorators import is_dataset_owner
from app.features.dataset.forms import DataSetForm
from app.features.dataset.models import DataSet, PublicationType
from app.features.dataset.services import (
    AuthorService,
    DatasetMetadataUpdateError,
    DatasetMetadataValidationError,
    DatasetOwnershipError,
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
from app.features.flamapy.services import FlamapyService
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
flamapy_service = FlamapyService()


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

# Hard cap for UVL payloads on the API-key write endpoints: the synchronous
# flamapy check parses slowly and with heavy memory amplification, so oversized
# models are rejected before reaching the parser.
UVL_MAX_BYTES = 1 * 1024 * 1024


def _check_uvl_content(uvl_content: str, filename: str | None) -> str | None:
    """Run the synchronous flamapy syntax check on raw UVL content.

    Returns None when the model parses, or a human-readable error message
    otherwise. The content is staged in a temp file because check_uvl works
    on file paths.
    """
    safe_name = secure_filename(os.path.basename(filename or "model.uvl")) or "model.uvl"
    if not safe_name.lower().endswith(".uvl"):
        safe_name = f"{safe_name}.uvl"

    check_dir = tempfile.mkdtemp(prefix="uvl_check_")
    try:
        check_path = os.path.join(check_dir, safe_name)
        with open(check_path, "w", encoding="utf-8", newline="\n") as check_file:
            check_file.write(uvl_content or "")
        result, status_code = flamapy_service.check_uvl(check_path)
        if status_code == 200:
            return None
        errors = result.get("errors") or [result.get("error") or "Invalid UVL model."]
        return " ".join(errors)
    finally:
        shutil.rmtree(check_dir, ignore_errors=True)


def _api_version_entry(dataset: DataSet, latest_id: int) -> dict:
    """One node of a version lineage as returned by the API.

    ``publication_date`` is the moment the version record was created, which is
    when it was published for datasets minted through the API. It is null while
    a version has no DOI, so an unpublished draft never looks published.
    """
    doi = dataset.ds_meta_data.dataset_doi
    return {
        "dataset_id": dataset.id,
        "version": dataset.dataset_version,
        "doi": doi,
        "publication_date": dataset.created_at.isoformat() if (doi and dataset.created_at) else None,
        "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
        "is_latest": dataset.id == latest_id,
    }


def _api_latest_of(lineage: list[DataSet]) -> DataSet:
    """The version a client should be sent to.

    Published versions win over unpublished ones. The last element of the
    lineage is not good enough on its own: a version whose publication failed
    would be advertised as the newest record with a null DOI, sending clients
    at something that does not exist on Zenodo.
    """
    published = [dataset for dataset in lineage if dataset.ds_meta_data.dataset_doi]
    return (published or lineage)[-1]


def _api_lineage_payload(lineage: list[DataSet]) -> dict:
    """Serialize a whole version lineage, oldest first."""
    latest = _api_latest_of(lineage)
    concept_doi = next(
        (ds.ds_meta_data.dataset_concept_doi for ds in lineage if ds.ds_meta_data.dataset_concept_doi),
        None,
    )
    return {
        "concept_doi": concept_doi,
        "total_versions": len(lineage),
        "latest": {
            "dataset_id": latest.id,
            "version": latest.dataset_version,
            "doi": latest.ds_meta_data.dataset_doi,
        },
        "versions": [_api_version_entry(dataset, latest.id) for dataset in lineage],
    }


def _api_dataset_files_payload(dataset: DataSet) -> list[dict]:
    """Serialize a dataset's files for API responses, with the public raw URL
    (/doi/<doi>/files/raw/<name>/) when the dataset has a DOI."""
    doi = dataset.ds_meta_data.dataset_doi
    host_url = request.host_url.rstrip("/")
    files = []
    for hubfile in dataset.files():
        entry = {"name": hubfile.name}
        if doi:
            entry["raw_url"] = f"{host_url}/doi/{doi}/files/raw/{hubfile.name}/"
        files.append(entry)
    return files


@dataset_bp.route("/api/v1/datasets/upload", methods=["POST"])
def api_upload_dataset():
    """
    Create a draft dataset from a UVL model
    ---
    tags:
      - Datasets
    security:
      - ApiKeyAuth: []
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
      - name: authors
        in: formData
        type: string
        required: false
        description: >
          Optional JSON array of authors to credit, each with name (required),
          affiliation and orcid; a plain string entry is read as a name. In a
          JSON body it is a real array. When omitted, the dataset is credited
          to the account owning the request, exactly as before. These authors
          are the creators sent to Zenodo on publication. An orcid is only
          accepted when that ORCID has signed in to uvlhub at least once, since
          it becomes a permanent public link to a named researcher; authors
          without one are credited by name. The publishing account is recorded
          and published in the Zenodo record's notes.
    responses:
      201:
        description: Draft dataset created successfully
      400:
        description: >
          Invalid import payload, invalid or unverifiable author data, or UVL
          that does not parse
      401:
        description: Authentication required
      403:
        description: API key invalid or missing the write_dataset scope
      413:
        description: UVL payload exceeds the 1 MB limit
    """

    # Two auth mechanisms: the flamapyIDE session (cookie) and an API key with
    # the write_dataset scope. Only the API-key path runs the synchronous
    # flamapy check, so the IDE flow keeps its current behaviour.
    authenticated_user = authentication_service.get_authenticated_user()
    api_key_user = None
    if not authenticated_user and request.headers.get("X-API-Key"):
        _, api_key_error = resolve_api_key("write_dataset")
        if api_key_error:
            return api_key_error
        api_key_user = g.api_user
        authenticated_user = api_key_user
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

    if api_key_user is not None and (uvl_content or "").strip():
        if len(uvl_content.encode("utf-8")) > UVL_MAX_BYTES:
            return jsonify({"error": "UVL file too large (max 1 MB)."}), 413
        uvl_error = _check_uvl_content(uvl_content, filename)
        if uvl_error:
            return jsonify({"error": uvl_error}), 400

    # Optional credit: the marketplace publishes with its own key while the
    # dataset is attributed to the real developer. Validated before anything
    # is written, same discipline as the UVL payload.
    try:
        authors = dataset_service.extract_authors_from_request(payload, request.form)
    except DatasetMetadataValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        dataset, created_fms = dataset_service.create_draft_from_uvl_import(
            current_user=authenticated_user,
            title=title,
            uvl_content=uvl_content,
            filename=filename,
            description=description,
            authors=authors,
            api_publisher=api_key_user,
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
                "authors": [author.to_dict() for author in dataset.ds_meta_data.authors],
                "edit_url": url_for("dataset.edit_metadata", dataset_id=dataset.id, _external=True),
                "view_url": url_for("dataset.get_unsynchronized_dataset", dataset_id=dataset.id, _external=True),
                "list_url": url_for("dataset.list_dataset", _external=True),
            }
        ),
        201,
    )


@dataset_bp.route("/api/v1/datasets/<int:dataset_id>/publish", methods=["POST"])
@require_api_key("write_dataset")
def api_publish_dataset(dataset_id):
    """
    Publish a draft dataset to Zenodo
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
        description: ID of the draft dataset to publish
    responses:
      200:
        description: Dataset published and indexed
        content:
          application/json:
            schema:
              type: object
              properties:
                doi:
                  type: string
                concept_doi:
                  type: string
                  nullable: true
                  description: Permanent DOI of the lineage, always resolving to the newest version
                deposition_id:
                  type: integer
                files:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                      raw_url:
                        type: string
              example:
                doi: "10.5072/zenodo.123"
                concept_doi: "10.5072/zenodo.122"
                deposition_id: 123
                files:
                  - name: "model.uvl"
                    raw_url: "https://www.uvlhub.io/doi/10.5072/zenodo.123/files/raw/model.uvl/"
      400:
        description: Dataset already published or Zenodo upload failed
      403:
        description: API key invalid, missing write_dataset scope, or not the dataset owner
      404:
        description: Dataset not found
    """
    dataset = dataset_service.get_by_id(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404
    if dataset.user_id != g.api_user.id:
        return jsonify({"error": "Forbidden: you do not own this dataset"}), 403
    if dataset.ds_meta_data.dataset_doi:
        return jsonify({"error": "Dataset already synchronized"}), 400

    zenodo_service_facade = ZenodoDatasetService(zenodo_service, dataset_service, logger)
    try:
        doi = zenodo_service_facade.upload_to_zenodo(dataset, dataset.ds_meta_data, "zenodo", g.api_user)
    except Exception as exc:
        logger.exception(f"[API PUBLISH ERROR] {exc}")
        return jsonify({"error": f"Zenodo upload failed: {exc}"}), 400

    indexing_service = IndexingService(index_dataset, index_hubfile, logger)
    try:
        dataset = dataset_service.get_by_id(dataset_id)
        indexing_service.index_dataset_and_hubfiles(dataset, dataset.feature_models)
    except Exception as exc:
        logger.warning(f"[API PUBLISH] Dataset {dataset_id} published, but indexing failed: {exc}")

    return (
        jsonify(
            {
                "message": "Dataset published successfully.",
                "dataset_id": dataset.id,
                "doi": doi,
                "concept_doi": dataset.ds_meta_data.dataset_concept_doi,
                "deposition_id": dataset.ds_meta_data.deposition_id,
                "files": _api_dataset_files_payload(dataset),
            }
        ),
        200,
    )


@dataset_bp.route("/api/v1/datasets/<int:dataset_id>/new-version", methods=["POST"])
@require_api_key("write_dataset")
def api_new_dataset_version(dataset_id):
    """
    Publish a new version of a published dataset with a replaced UVL
    ---
    tags:
      - Datasets
    security:
      - ApiKeyAuth: []
    consumes:
      - multipart/form-data
    parameters:
      - name: dataset_id
        in: path
        type: integer
        required: true
        description: ID of the published dataset to version
      - name: file
        in: formData
        type: file
        required: true
        description: Replacement .uvl file for the new version
    responses:
      200:
        description: New version published to Zenodo
        content:
          application/json:
            schema:
              type: object
              properties:
                doi:
                  type: string
                concept_doi:
                  type: string
                  nullable: true
                  description: Same permanent DOI as every other version of this dataset
                version:
                  type: integer
                files:
                  type: array
                  items:
                    type: object
              example:
                doi: "10.5072/zenodo.124"
                concept_doi: "10.5072/zenodo.122"
                version: 2
                files:
                  - name: "model_v2.uvl"
                    raw_url: "https://www.uvlhub.io/doi/10.5072/zenodo.124/files/raw/model_v2.uvl/"
      400:
        description: Missing or invalid .uvl file, dataset not published yet, or Zenodo failure
      403:
        description: API key invalid, missing write_dataset scope, or not the dataset owner
      404:
        description: Dataset not found
      413:
        description: UVL payload exceeds the 1 MB limit
    """
    dataset = dataset_service.get_by_id(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404
    if dataset.user_id != g.api_user.id:
        return jsonify({"error": "Forbidden: you do not own this dataset"}), 403

    uploaded_file = request.files.get("file")
    if uploaded_file is None:
        return jsonify({"error": "A .uvl file is required."}), 400

    # Validate the replacement UVL before touching Zenodo: a new version mints
    # a permanent DOI, so garbage must be rejected here.
    raw_content = uploaded_file.read()
    if len(raw_content) > UVL_MAX_BYTES:
        return jsonify({"error": "UVL file too large (max 1 MB)."}), 413
    try:
        uvl_content = raw_content.decode("utf-8")
    except UnicodeDecodeError:
        return jsonify({"error": "UVL file must be UTF-8 encoded."}), 400
    uvl_error = _check_uvl_content(uvl_content, uploaded_file.filename)
    if uvl_error:
        return jsonify({"error": uvl_error}), 400
    # create_new_version re-reads the file, so rewind after the checks.
    uploaded_file.stream.seek(0)

    try:
        new_dataset = dataset_service.create_new_version(
            dataset, uploaded_file, g.api_user, zenodo_service=zenodo_service
        )
    except (DatasetMetadataValidationError, DatasetMetadataUpdateError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001 - surface Zenodo/versioning failures to the client
        logger.exception("[API NEW VERSION] Unexpected error for dataset %s", dataset_id)
        return jsonify({"error": f"Unexpected error creating the new version: {exc}"}), 400

    indexing_service = IndexingService(index_dataset, index_hubfile, logger)
    try:
        indexing_service.index_dataset_and_hubfiles(new_dataset, new_dataset.feature_models)
    except Exception as exc:
        logger.warning(f"[API NEW VERSION] Dataset {new_dataset.id} versioned, but indexing failed: {exc}")

    return (
        jsonify(
            {
                "message": "New version published to Zenodo.",
                "dataset_id": new_dataset.id,
                "doi": new_dataset.ds_meta_data.dataset_doi,
                "concept_doi": new_dataset.ds_meta_data.dataset_concept_doi,
                "version": new_dataset.dataset_version,
                "files": _api_dataset_files_payload(new_dataset),
            }
        ),
        200,
    )


def _resolve_transfer_target(payload: dict):
    """Find the account a transfer is aimed at, or an error response.

    ``user_id`` is parsed strictly. A permissive ``int()`` accepts JSON true
    (1) and 1.9 (1), which would offer the dataset to whichever account holds
    that id instead of failing, so anything that is not a whole number is
    rejected outright.
    """
    raw_user_id = payload.get("user_id", request.form.get("user_id"))
    raw_email = payload.get("email", request.form.get("email"))

    if raw_user_id not in (None, ""):
        user_id = _parse_strict_int(raw_user_id)
        if user_id is None:
            return None, (jsonify({"error": "user_id must be an integer."}), 400)
        return authentication_service.get_by_id(user_id), None

    if raw_email:
        if not isinstance(raw_email, str):
            return None, (jsonify({"error": "email must be a string."}), 400)
        # active=None so a deactivated account is reported as such instead of
        # looking like a typo in the email.
        return authentication_service.get_by_email(raw_email, active=None), None

    return None, (jsonify({"error": "A target account is required (user_id or email)."}), 400)


def _parse_strict_int(value):
    """Whole numbers only, in either JSON or form shape.

    bool is a subclass of int in Python and float truncates, so both slip past
    ``int(value)`` untouched and hand the dataset to the wrong account. Only an
    actual integer, or a string of digits, is accepted.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.lstrip("+-").isdigit():
            return int(text)
    return None


def _transfer_payload(transfer, extra: dict | None = None) -> dict:
    body = transfer.to_dict()
    if extra:
        body.update(extra)
    return body


@dataset_bp.route("/api/v1/datasets/<int:dataset_id>/transfer", methods=["POST"])
@require_api_key("write_dataset")
def api_transfer_dataset_ownership(dataset_id):
    """
    Offer a dataset and its whole version lineage to another account
    ---
    tags:
      - Datasets
    security:
      - ApiKeyAuth: []
    consumes:
      - application/json
      - multipart/form-data
    parameters:
      - name: dataset_id
        in: path
        type: integer
        required: true
        description: ID of any version of the lineage to transfer
      - name: user_id
        in: formData
        type: integer
        required: false
        description: ID of the account the dataset is offered to
      - name: email
        in: formData
        type: string
        required: false
        description: Email of the account the dataset is offered to, when user_id is not known
      - name: message
        in: formData
        type: string
        required: false
        description: Optional note shown to the receiving account
    responses:
      202:
        description: >
          Offer created and waiting for the receiving account to answer.
          Nothing has changed owner yet.
        content:
          application/json:
            schema:
              type: object
              properties:
                transfer_id:
                  type: integer
                status:
                  type: string
                dataset_id:
                  type: integer
                from_user_id:
                  type: integer
                to_user_id:
                  type: integer
                lineage_dataset_ids:
                  type: array
                  items:
                    type: integer
              example:
                message: "Transfer offered. It moves once the receiving account accepts."
                transfer_id: 12
                status: "pending"
                dataset_id: 4
                from_user_id: 1
                to_user_id: 7
                lineage_dataset_ids: [4, 9]
      400:
        description: >
          No target account given, target equals the current owner, an offer is
          already pending, or the lineage cannot be moved
      403:
        description: API key invalid, missing write_dataset scope, or not the dataset owner
      404:
        description: Dataset or target account not found
    """
    dataset = dataset_service.get_by_id(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404
    if dataset.user_id != g.api_user.id:
        return jsonify({"error": "Forbidden: you do not own this dataset"}), 403

    payload = request.get_json(silent=True) if request.is_json else {}
    payload = payload or {}

    new_owner, error = _resolve_transfer_target(payload)
    if error:
        return error
    if new_owner is None:
        return jsonify({"error": "Target account not found"}), 404
    if not new_owner.active:
        return jsonify({"error": "The target account is not active."}), 400

    note = payload.get("message", request.form.get("message"))
    if note is not None and not isinstance(note, str):
        return jsonify({"error": "message must be a string."}), 400

    try:
        transfer = dataset_service.request_ownership_transfer(dataset, g.api_user, new_owner, message=note)
    except DatasetOwnershipError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001 - surface storage/DB failures to the client
        logger.exception("[API TRANSFER] Unexpected error offering dataset %s", dataset_id)
        return jsonify({"error": f"Unexpected error offering the transfer: {exc}"}), 400

    lineage = dataset_service.get_lineage(dataset)
    return (
        jsonify(
            _transfer_payload(
                transfer,
                {
                    "message": "Transfer offered. It moves once the receiving account accepts.",
                    "lineage_dataset_ids": [version.id for version in lineage],
                },
            )
        ),
        202,
    )


@dataset_bp.route("/api/v1/datasets/transfers", methods=["GET"])
@require_api_key("read_dataset")
def api_list_dataset_transfers():
    """
    List the dataset transfers this account sent or received
    ---
    tags:
      - Datasets
    security:
      - ApiKeyAuth: []
    parameters:
      - name: status
        in: query
        type: string
        required: false
        description: Filter by status (pending, accepted, declined, cancelled)
    responses:
      200:
        description: Transfers involving this account, newest first
        content:
          application/json:
            schema:
              type: object
              properties:
                incoming:
                  type: array
                  items:
                    type: object
                outgoing:
                  type: array
                  items:
                    type: object
              example:
                incoming:
                  - transfer_id: 12
                    dataset_id: 4
                    from_user_id: 1
                    to_user_id: 7
                    status: "pending"
                    message: null
                    created_at: "2026-07-26T10:00:00+00:00"
                    resolved_at: null
                outgoing: []
      400:
        description: Unknown status filter
      403:
        description: API key invalid or missing the read_dataset scope
    """
    try:
        transfers = dataset_service.get_transfer_requests_for_user(g.api_user.id, request.args.get("status"))
    except DatasetOwnershipError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(
        {
            "incoming": [t.to_dict() for t in transfers if t.to_user_id == g.api_user.id],
            "outgoing": [t.to_dict() for t in transfers if t.from_user_id == g.api_user.id],
        }
    )


def _load_transfer_or_error(transfer_id):
    transfer = dataset_service.get_transfer_request(transfer_id)
    if transfer is None:
        return None, (jsonify({"error": "Transfer not found"}), 404)
    if g.api_user.id not in (transfer.from_user_id, transfer.to_user_id):
        # Not a party to it, so it does not exist as far as this key is concerned.
        return None, (jsonify({"error": "Transfer not found"}), 404)
    return transfer, None


@dataset_bp.route("/api/v1/datasets/transfers/<int:transfer_id>/accept", methods=["POST"])
@require_api_key("write_dataset")
def api_accept_dataset_transfer(transfer_id):
    """
    Accept a dataset offered to this account and take over its whole lineage
    ---
    tags:
      - Datasets
    security:
      - ApiKeyAuth: []
    parameters:
      - name: transfer_id
        in: path
        type: integer
        required: true
        description: ID of the pending transfer
    responses:
      200:
        description: Ownership transferred
        content:
          application/json:
            schema:
              type: object
              properties:
                transfer_id:
                  type: integer
                status:
                  type: string
                previous_owner_id:
                  type: integer
                new_owner_id:
                  type: integer
                transferred_dataset_ids:
                  type: array
                  items:
                    type: integer
              example:
                message: "Ownership transferred."
                transfer_id: 12
                status: "accepted"
                dataset_id: 4
                previous_owner_id: 1
                new_owner_id: 7
                transferred_dataset_ids: [4, 9]
      400:
        description: Transfer already resolved, or the lineage cannot be moved
      403:
        description: API key invalid, missing write_dataset scope, or not the receiving account
      404:
        description: Transfer not found
    """
    transfer, error = _load_transfer_or_error(transfer_id)
    if error:
        return error
    if transfer.to_user_id != g.api_user.id:
        return jsonify({"error": "Forbidden: this dataset was not offered to you"}), 403

    previous_owner_id = transfer.from_user_id
    try:
        lineage = dataset_service.accept_ownership_transfer(transfer, g.api_user)
    except DatasetOwnershipError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001 - surface storage/DB failures to the client
        logger.exception("[API TRANSFER] Unexpected error accepting transfer %s", transfer_id)
        return jsonify({"error": f"Unexpected error transferring ownership: {exc}"}), 400

    return (
        jsonify(
            _transfer_payload(
                transfer,
                {
                    "message": "Ownership transferred.",
                    "previous_owner_id": previous_owner_id,
                    "new_owner_id": g.api_user.id,
                    "transferred_dataset_ids": [version.id for version in lineage],
                    "versions": _api_lineage_payload(lineage)["versions"],
                },
            )
        ),
        200,
    )


@dataset_bp.route("/api/v1/datasets/transfers/<int:transfer_id>/decline", methods=["POST"])
@require_api_key("write_dataset")
def api_decline_dataset_transfer(transfer_id):
    """
    Decline a dataset offered to this account
    ---
    tags:
      - Datasets
    security:
      - ApiKeyAuth: []
    parameters:
      - name: transfer_id
        in: path
        type: integer
        required: true
        description: ID of the pending transfer
    responses:
      200:
        description: Offer declined, nothing changed owner
        content:
          application/json:
            schema:
              type: object
              example:
                message: "Transfer declined."
                transfer_id: 12
                status: "declined"
                dataset_id: 4
      400:
        description: Transfer already resolved
      403:
        description: API key invalid, missing write_dataset scope, or not the receiving account
      404:
        description: Transfer not found
    """
    transfer, error = _load_transfer_or_error(transfer_id)
    if error:
        return error
    if transfer.to_user_id != g.api_user.id:
        return jsonify({"error": "Forbidden: this dataset was not offered to you"}), 403

    try:
        dataset_service.decline_ownership_transfer(transfer, g.api_user)
    except DatasetOwnershipError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(_transfer_payload(transfer, {"message": "Transfer declined."})), 200


@dataset_bp.route("/api/v1/datasets/transfers/<int:transfer_id>/cancel", methods=["POST"])
@require_api_key("write_dataset")
def api_cancel_dataset_transfer(transfer_id):
    """
    Withdraw a transfer this account offered
    ---
    tags:
      - Datasets
    security:
      - ApiKeyAuth: []
    parameters:
      - name: transfer_id
        in: path
        type: integer
        required: true
        description: ID of the pending transfer
    responses:
      200:
        description: Offer withdrawn
        content:
          application/json:
            schema:
              type: object
              example:
                message: "Transfer cancelled."
                transfer_id: 12
                status: "cancelled"
                dataset_id: 4
      400:
        description: Transfer already resolved
      403:
        description: API key invalid, missing write_dataset scope, or not the offering account
      404:
        description: Transfer not found
    """
    transfer, error = _load_transfer_or_error(transfer_id)
    if error:
        return error
    if transfer.from_user_id != g.api_user.id:
        return jsonify({"error": "Forbidden: you did not offer this dataset"}), 403

    try:
        dataset_service.cancel_ownership_transfer(transfer, g.api_user)
    except DatasetOwnershipError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(_transfer_payload(transfer, {"message": "Transfer cancelled."})), 200


@dataset_bp.route("/api/v1/datasets/doi/<path:doi>", methods=["GET"])
@require_api_key("read_dataset")
def api_dataset_by_doi(doi):
    """
    Get a dataset by DOI
    ---
    tags:
      - Datasets
    security:
      - ApiKeyAuth: []
    parameters:
      - name: doi
        in: path
        type: string
        required: true
        description: DOI of the dataset to retrieve
    responses:
      200:
        description: Dataset matching the DOI, with its position in the version lineage
        content:
          application/json:
            schema:
              type: object
              properties:
                dataset_id:
                  type: integer
                doi:
                  type: string
                title:
                  type: string
                concept_doi:
                  type: string
                  nullable: true
                  description: Permanent DOI of the lineage, always resolving to the newest version
                version:
                  type: integer
                is_latest:
                  type: boolean
                latest:
                  type: object
                  properties:
                    dataset_id:
                      type: integer
                    version:
                      type: integer
                    doi:
                      type: string
                      nullable: true
                files:
                  type: array
                  items:
                    type: object
              example:
                dataset_id: 4
                doi: "10.5072/zenodo.123"
                title: "My Dataset"
                concept_doi: "10.5072/zenodo.122"
                version: 1
                is_latest: false
                latest:
                  dataset_id: 9
                  version: 2
                  doi: "10.5072/zenodo.456"
                files:
                  - name: "model.uvl"
                    raw_url: "https://www.uvlhub.io/doi/10.5072/zenodo.123/files/raw/model.uvl/"
      404:
        description: No dataset with that DOI
    """
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)
    if not ds_meta_data or not ds_meta_data.dataset:
        return jsonify({"error": "Dataset not found"}), 404

    dataset = ds_meta_data.dataset
    lineage = dataset_service.get_lineage(dataset)
    lineage_payload = _api_lineage_payload(lineage)

    # Additive only: dataset_id, doi, title and files keep their meaning and
    # position so existing clients are unaffected.
    return jsonify(
        {
            "dataset_id": dataset.id,
            "doi": ds_meta_data.dataset_doi,
            "title": ds_meta_data.title,
            "files": _api_dataset_files_payload(dataset),
            "concept_doi": lineage_payload["concept_doi"],
            "version": dataset.dataset_version,
            "total_versions": lineage_payload["total_versions"],
            "is_latest": dataset.id == lineage_payload["latest"]["dataset_id"],
            "latest": lineage_payload["latest"],
            "versions_url": url_for("dataset.api_dataset_versions", dataset_id=dataset.id, _external=True),
        }
    )


@dataset_bp.route("/api/v1/datasets/<int:dataset_id>/versions", methods=["GET"])
@require_api_key("read_dataset")
def api_dataset_versions(dataset_id):
    """
    List the whole version lineage of a dataset
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
        description: ID of any version of the lineage
    responses:
      200:
        description: Every version of the lineage, oldest first
        content:
          application/json:
            schema:
              type: object
              properties:
                dataset_id:
                  type: integer
                concept_doi:
                  type: string
                  nullable: true
                total_versions:
                  type: integer
                latest:
                  type: object
                versions:
                  type: array
                  items:
                    type: object
                    properties:
                      dataset_id:
                        type: integer
                      version:
                        type: integer
                      doi:
                        type: string
                        nullable: true
                      publication_date:
                        type: string
                        format: date-time
                        nullable: true
                      is_latest:
                        type: boolean
              example:
                dataset_id: 4
                concept_doi: "10.5072/zenodo.122"
                total_versions: 2
                latest:
                  dataset_id: 9
                  version: 2
                  doi: "10.5072/zenodo.456"
                versions:
                  - dataset_id: 4
                    version: 1
                    doi: "10.5072/zenodo.123"
                    publication_date: "2026-07-01T10:00:00+00:00"
                    created_at: "2026-07-01T10:00:00+00:00"
                    is_latest: false
                  - dataset_id: 9
                    version: 2
                    doi: "10.5072/zenodo.456"
                    publication_date: "2026-07-20T09:30:00+00:00"
                    created_at: "2026-07-20T09:30:00+00:00"
                    is_latest: true
      404:
        description: Dataset not found
    """
    dataset = dataset_service.get_by_id(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404

    payload = _api_lineage_payload(dataset_service.get_lineage(dataset))
    payload["dataset_id"] = dataset.id
    return jsonify(payload)


@dataset_bp.route("/api/v1/datasets/concept-doi/<path:concept_doi>", methods=["GET"])
@require_api_key("read_dataset")
def api_dataset_lineage_by_concept_doi(concept_doi):
    """
    Resolve a version lineage by its concept DOI
    ---
    tags:
      - Datasets
    security:
      - ApiKeyAuth: []
    parameters:
      - name: concept_doi
        in: path
        type: string
        required: true
        description: Concept DOI shared by every version of the lineage
    responses:
      200:
        description: Every version of the lineage, oldest first
        content:
          application/json:
            schema:
              type: object
              properties:
                concept_doi:
                  type: string
                total_versions:
                  type: integer
                latest:
                  type: object
                versions:
                  type: array
                  items:
                    type: object
              example:
                concept_doi: "10.5072/zenodo.122"
                total_versions: 2
                latest:
                  dataset_id: 9
                  version: 2
                  doi: "10.5072/zenodo.456"
                versions:
                  - dataset_id: 4
                    version: 1
                    doi: "10.5072/zenodo.123"
                    publication_date: "2026-07-01T10:00:00+00:00"
                    created_at: "2026-07-01T10:00:00+00:00"
                    is_latest: false
                  - dataset_id: 9
                    version: 2
                    doi: "10.5072/zenodo.456"
                    publication_date: "2026-07-20T09:30:00+00:00"
                    created_at: "2026-07-20T09:30:00+00:00"
                    is_latest: true
      404:
        description: No lineage with that concept DOI
    """
    lineage = dataset_service.get_lineage_by_concept_doi(concept_doi)
    if not lineage:
        return jsonify({"error": "Dataset not found"}), 404

    payload = _api_lineage_payload(lineage)
    payload["concept_doi"] = concept_doi
    return jsonify(payload)


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
