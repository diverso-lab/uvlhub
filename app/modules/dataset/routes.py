from datetime import datetime
import logging
import os
import json
import shutil
import tempfile

from flask import (
    abort,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from flask_login import login_required, current_user

from app.modules.dataset.decorators import is_dataset_owner
from app.modules.dataset.forms import DataSetForm
from app.modules.dataset import dataset_bp
from app.modules.dataset.services import (
    AuthorService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
    DataSetService,
    DOIMappingService
)
from app.modules.hubfile.services import HubfileService
from app.modules.zenodo.services import ZenodoService

logger = logging.getLogger(__name__)


dataset_service = DataSetService()
author_service = AuthorService()
dsmetadata_service = DSMetaDataService()
zenodo_service = ZenodoService()
doi_mapping_service = DOIMappingService()
ds_view_record_service = DSViewRecordService()
ds_download_record_service = DSDownloadRecordService()
hubfile_service = HubfileService()


@dataset_bp.route("/dataset/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = DataSetForm()
    if request.method == "POST":

        dataset = None

        if not form.validate_on_submit():
            return jsonify({"message": form.errors}), 400

        try:
            logger.info("Creating dataset...")
            dataset = dataset_service.create_from_form(form=form, current_user=current_user)
            logger.info(f"Created dataset: {dataset}")
            dataset_service.move_feature_models(dataset)
        except Exception as exc:
            logger.exception(f"Exception while create dataset data in local {exc}")
            return jsonify({"Exception while create dataset data in local: ": str(exc)}), 400

        # send dataset as deposition to Zenodo
        data = {}
        try:
            zenodo_response_json = zenodo_service.create_new_deposition(dataset)
            response_data = json.dumps(zenodo_response_json)
            data = json.loads(response_data)
        except Exception as exc:
            data = {}
            zenodo_response_json = {}
            logger.exception(f"Exception while create dataset data in Zenodo {exc}")

        if data.get("conceptrecid"):
            deposition_id = data.get("id")

            # update dataset with deposition id in Zenodo
            dataset_service.update_dsmetadata(dataset.ds_meta_data_id, deposition_id=deposition_id)

            try:
                # iterate for each feature model (one feature model = one request to Zenodo)
                for feature_model in dataset.feature_models:
                    zenodo_service.upload_file(dataset, deposition_id, feature_model)

                # publish deposition
                zenodo_service.publish_deposition(deposition_id)

                # update DOI
                deposition_doi = zenodo_service.get_doi(deposition_id)
                dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=deposition_doi)
            except Exception as e:
                msg = f"it has not been possible upload feature models in Zenodo and update the DOI: {e}"
                return jsonify({"message": msg}), 200

        # Delete temp folder
        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Everything works!"
        return jsonify({"message": msg}), 200

    with_hubfiles = request.args.get("with_hubfiles", "")
    hubfiles_ids = [int(x) for x in with_hubfiles.split(",") if x]
    hubfiles = hubfile_service.get_by_ids(hubfiles_ids)

    return render_template(
        "dataset/create_and_edit_dataset.html", form=form, hubfiles=[hub.to_dict() for hub in hubfiles]
    )


@dataset_bp.route("/dataset/edit/<int:dataset_id>", methods=["GET"])
@login_required
@is_dataset_owner
def edit_dataset(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)
    form = DataSetForm(obj=dataset)
    form = dataset_service.populate_form_from_dataset(form=form, dataset=dataset)
    is_edit = True
    return render_template("dataset/create_and_edit_dataset.html", form=form,
                           is_edit=is_edit,
                           dataset=dataset,
                           enumerate=enumerate)


@dataset_bp.route("/dataset/update", methods=["POST"])
@login_required
def update_dataset():

    form = DataSetForm()
    dataset_id = request.form.get('datasetId')
    dataset = dataset_service.get_by_id(dataset_id)

    if dataset is None:
        abort(404)

    if dataset.user_id != current_user.id:
        abort(404)

    logger.info(f"[BACK] Dataset: {dataset.id}")

    if not form.validate_on_submit():
        logger.info(f"Form errors: {form.errors}")
        return jsonify({"message": form.errors}), 400

    try:
        logger.info("Updating dataset...")
        dataset = dataset_service.update_from_form(form=form, current_user=current_user, dataset=dataset)
        logger.info(f"Updating deposition with id {dataset.get_zenodo_deposition()}")
    except Exception as exc:
        logger.exception(f"Exception while saving dataset data in local {exc}")
        return jsonify({"Exception while saving dataset data in local: ": str(exc)}), 400

    try:
        zenodo_service.update_deposition(deposition_id=dataset.get_zenodo_deposition(),
                                         metadata=dataset.get_zenodo_metadata())
    except Exception as exc:
        logger.exception(f"Exception while update deposition in Zenodo: {exc}")

    msg = "[Back] Everything works!"
    return jsonify({"message": msg}), 200


@dataset_bp.route("/dataset/list", methods=["GET"])
@login_required
def list_dataset():
    return render_template(
        "dataset/list_datasets.html",
        datasets=dataset_service.get_synchronized_datasets_by_user(current_user.id),
        local_datasets=dataset_service.get_unsynchronized_datasets_by_user(current_user.id),
    )


@dataset_bp.route("/dataset/download/<int:dataset_id>", methods=["GET"])
def download_dataset(dataset_id):

    dataset = dataset_service.get_or_404(dataset_id)

    temp_dir = dataset_service.zip_dataset(dataset)

    user_cookie = ds_download_record_service.create_cookie(dataset)

    resp = make_response(
        send_from_directory(
            temp_dir,
            f"dataset_{dataset.id}.zip",
            as_attachment=True,
            mimetype="application/zip",
        )
    )

    resp.set_cookie("download_cookie", user_cookie)

    return resp


@dataset_bp.route("/dataset/download/all", methods=["GET"])
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


@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):

    # Check if the DOI is an old DOI
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        # Redirect to the same path with the new DOI
        return redirect(url_for('dataset.subdomain_index', doi=new_doi), code=302)

    # Try to search the dataset by the provided DOI (which should already be the new one)
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)

    if not ds_meta_data:
        abort(404)

    # Get dataset
    dataset = ds_meta_data.data_set

    # Save the cookie to the user's browser
    user_cookie = ds_view_record_service.create_cookie(dataset=dataset)
    resp = make_response(render_template("dataset/view_dataset.html", dataset=dataset))
    resp.set_cookie("view_cookie", user_cookie)

    return resp


@dataset_bp.route("/dataset/unsynchronized/<int:dataset_id>/", methods=["GET"])
@login_required
def get_unsynchronized_dataset(dataset_id):

    # Get dataset
    dataset = dataset_service.get_unsynchronized_dataset_by_user(current_user.id, dataset_id)

    if not dataset:
        abort(404)

    return render_template("dataset/view_dataset.html", dataset=dataset)
