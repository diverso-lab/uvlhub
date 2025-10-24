import logging
import os
import shutil
import tempfile
from datetime import datetime

from flask import abort, current_app, jsonify, make_response, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from app.modules.apikeys.decorators import require_api_key
from app.modules.dataset import dataset_bp
from app.modules.dataset.decorators import is_dataset_owner
from app.modules.dataset.forms import DataSetForm
from app.modules.dataset.models import DataSet
from app.modules.dataset.services import (
    AuthorService,
    DataSetService,
    DOIMappingService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
    LocalDatasetService,
)
from app.modules.elasticsearch.services import IndexingService
from app.modules.elasticsearch.utils import index_dataset, index_hubfile
from app.modules.featuremodel.services import FeatureModelService
from app.modules.hubfile.models import Hubfile
from app.modules.hubfile.services import HubfileService
from app.modules.zenodo.services import ZenodoDatasetService, ZenodoService

logger = logging.getLogger(__name__)


dataset_service = DataSetService()
author_service = AuthorService()
dsmetadata_service = DSMetaDataService()
zenodo_service = ZenodoService()
doi_mapping_service = DOIMappingService()
ds_view_record_service = DSViewRecordService()
ds_download_record_service = DSDownloadRecordService()
hubfile_service = HubfileService()


@dataset_bp.route("/datasets/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = DataSetForm()

    if request.method == "POST":
        dataset_type = request.form.get("dataset_type", "draft")

        # 1. Crear dataset local
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

        # 2. Draft → terminar aquí
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

            # 4. Indexación
            indexing_service = IndexingService(index_dataset, index_hubfile, logger)
            try:
                dataset = dataset_service.get_by_id(dataset.id)  # actualizado tras Zenodo
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
    return render_template("dataset/create_and_edit_dataset.html", form=form)


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

    zip_path = dataset_service.zip_from_storage(dataset)

    if not zip_path or not os.path.exists(zip_path):
        abort(404, description="ZIP file not found.")

    user_cookie = ds_download_record_service.create_cookie(dataset)

    resp = make_response(send_file(zip_path, as_attachment=True, mimetype="application/zip"))
    resp.set_cookie("download_cookie", user_cookie)
    return resp


@dataset_bp.route("/datasets/download/all", methods=["GET"])
def download_all_dataset():
    # Crear un directorio temporal
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "all_datasets.zip")

    try:
        # Generar el archivo ZIP
        dataset_service.zip_all_datasets(zip_path)

        # Crear el nombre del archivo con la fecha
        current_date = datetime.now().strftime("%Y_%m_%d")
        zip_filename = f"uvlhub_bulk_{current_date}.zip"

        # Enviar el archivo como respuesta
        return send_file(zip_path, as_attachment=True, download_name=zip_filename)
    finally:
        # Asegurar que la carpeta temporal se elimine después de que Flask sirva el archivo
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


@dataset_bp.route("/doi/<path:doi>", methods=["GET"])
@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):
    # Redirección si el DOI es antiguo
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        return redirect(url_for("dataset.subdomain_index", doi=new_doi), code=302)

    # Buscar el dataset por DOI
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)
    if not ds_meta_data:
        abort(404)

    dataset = ds_meta_data.dataset

    # Obtener todos los hubfiles de los feature models
    hubfiles = []
    for fm in dataset.feature_models:
        hubfiles.extend(fm.hubfiles)

    # Guardar la cookie
    user_cookie = ds_view_record_service.create_cookie(dataset=dataset)

    # Renderizar vista con todos los datos
    resp = make_response(render_template("dataset/view_dataset.html", dataset=dataset, hubfiles=hubfiles))
    resp.set_cookie("view_cookie", user_cookie)

    return resp


@dataset_bp.route("/datasets/unsynchronized/<int:dataset_id>/", methods=["GET"])
@login_required
@is_dataset_owner
def get_unsynchronized_dataset(dataset_id):

    # Get dataset
    dataset = dataset_service.get_unsynchronized_dataset_by_user(current_user.id, dataset_id)

    # Obtener todos los hubfiles de los feature models
    hubfiles = []
    for fm in dataset.feature_models:
        hubfiles.extend(fm.hubfiles)

    if not dataset:
        abort(404)

    return render_template("dataset/view_dataset.html", dataset=dataset, hubfiles=hubfiles)


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
        # redirección visual
        return redirect(url_for("dataset.list_dataset"))
    else:
        # respuesta JSON (útil si luego quieres AJAX)
        return jsonify({"message": "Dataset synchronized", "doi": doi}), 200


# REST API


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

    pagination = DataSet.query.paginate(page=page, per_page=per_page, error_out=False)
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
    dataset = DataSet.query.get(dataset_id)
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
    dataset = DataSet.query.get(dataset_id)
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
    dataset = DataSet.query.get(dataset_id)
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
    file = Hubfile.query.get(file_id)
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
    file = Hubfile.query.get(file_id)
    if not file:
        return jsonify({"error": "File not found"}), 404

    dataset = file.feature_model.dataset

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
    file = Hubfile.query.get(file_id)
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
