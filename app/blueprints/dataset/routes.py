import os
import json
import hashlib
import shutil
import tempfile
import uuid
from datetime import datetime
from zipfile import ZipFile

from flask import (
    render_template,
    request,
    jsonify,
    send_from_directory,
    current_app,
    make_response,
    abort,
)
from flask_login import login_required, current_user

import app
from app.blueprints.dataset.forms import DataSetForm
from app.blueprints.dataset.models import DataSet, PublicationType
from app.blueprints.dataset import dataset_bp
from app.blueprints.dataset.repositories import (
    AuthorRepository,
    DSDownloadRecordRepository,
    DSMetaDataRepository,
    DSViewRecordRepository,
    DataSetRepository,
    FMMetaDataRepository,
    FeatureModelRepository,
    FileRepository,
    FileDownloadRecordRepository,
)
from app.blueprints.zenodo.services import ZenodoService


zenodo_service = ZenodoService()


@dataset_bp.route("/dataset/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = DataSetForm()
    if request.method == "POST":
        try:
            # get JSON from frontend
            form_data_json = request.form.get("formData")
            form_data_dict = json.loads(form_data_json)

            # get dicts
            uploaded_models_data = form_data_dict["uploaded_models_form"]

            # create dataset
            dataset = create_dataset_in_db(form_data_dict["basic_info_form"])

            # send dataset as deposition to Zenodo
            try:
                zenodo_response_json = zenodo_service.create_new_deposition(dataset)
                response_data = json.dumps(zenodo_response_json)
                data = json.loads(response_data)
            except Exception:
                data = {}

            if data.get("conceptrecid"):
                deposition_id = data.get("id")

                # update dataset with deposition id in Zenodo
                DSMetaDataRepository().update(
                    dataset.ds_meta_data_id, deposition_id=deposition_id
                )

                # create feature models
                feature_models = create_feature_models_in_db(
                    dataset, uploaded_models_data
                )

                try:
                    # iterate for each feature model (one feature model = one request to Zenodo
                    for feature_model in feature_models:
                        zenodo_service.upload_file(deposition_id, feature_model)

                    # publish deposition
                    zenodo_service.publish_deposition(deposition_id)

                    # update DOI
                    deposition_doi = zenodo_service.get_doi(deposition_id)
                    DSMetaDataRepository().update(
                        dataset.ds_meta_data_id, dataset_doi=deposition_doi
                    )
                except Exception:
                    pass

                # move feature models permanently
                move_feature_models(dataset.id, feature_models)

            else:
                # it has not been possible to create the deposition in Zenodo, so we save everything locally

                # create feature models
                feature_models = create_feature_models_in_db(
                    dataset, uploaded_models_data
                )

                # move feature models permanently
                move_feature_models(dataset.id, feature_models)

            return jsonify({"message": zenodo_response_json}), 200

        except Exception as e:
            return jsonify({"message": str(e)}), 500

    # Delete temp folder
    file_path = os.path.join(app.upload_folder_name(), "temp", str(current_user.id))
    if os.path.exists(file_path) and os.path.isdir(file_path):
        shutil.rmtree(file_path)

    return render_template("dataset/upload_dataset.html", form=form)


@dataset_bp.route("/dataset/list", methods=["GET", "POST"])
@login_required
def list_dataset():
    return render_template(
        "dataset/list_datasets.html",
        datasets=DataSetRepository().get_synchronized(current_user.id),
        local_datasets=DataSetRepository().get_unsynchronized(current_user.id),
    )


def create_dataset_in_db(basic_info_data):
    ds_data = {
        "title": basic_info_data["title"][0],
        "description": basic_info_data["description"][0],
        "publication_type": PublicationType(basic_info_data["publication_type"][0]),
        "publication_doi": basic_info_data["publication_doi"][0],
        "tags": basic_info_data["tags"][0],
    }
    ds_meta_data = DSMetaDataRepository().create(**ds_data)

    # create dataset metadata authors
    # I always add myself
    author_data = {
        "name": f"{current_user.profile.surname}, {current_user.profile.name}",
        "affiliation": current_user.profile.affiliation
        if hasattr(current_user.profile, "affiliation")
        else None,
        "orcid": current_user.profile.orcid
        if hasattr(current_user.profile, "orcid")
        else None,
        "ds_meta_data_id": ds_meta_data.id,
    }
    AuthorRepository().create(**author_data)

    # how many authors are there?
    if "author_name" in basic_info_data:
        number_of_authors = len(basic_info_data["author_name"])
        for i in range(number_of_authors):
            extra_author = {
                "name": basic_info_data["author_name"][i],
                "affiliation": basic_info_data["author_affiliation"][i],
                "orcid": basic_info_data["author_orcid"][i],
                "ds_meta_data_id": ds_meta_data.id,
            }
            AuthorRepository().create(**extra_author)

    # create dataset
    return DataSetRepository().create(
        user_id=current_user.id, ds_meta_data_id=ds_meta_data.id
    )


def create_feature_models_in_db(dataset: DataSet, uploaded_models_data: dict):
    feature_models = []

    for i, uvl_identifier in enumerate(uploaded_models_data.get("uvl_identifier", [])):
        uvl_filename = uploaded_models_data["uvl_filename"][i]

        # create feature model metadata
        feature_model_metadata = FMMetaDataRepository().create(
            uvl_filename=uvl_filename,
            title=uploaded_models_data["title"][i],
            description=uploaded_models_data["description"][i],
            publication_type=PublicationType(
                uploaded_models_data["uvl_publication_type"][i]
            ),
            publication_doi=uploaded_models_data["publication_doi"][i],
            tags=uploaded_models_data["tags"][i],
            uvl_version=uploaded_models_data["uvl_version"][i],
        )

        # create feature model
        feature_model = FeatureModelRepository().create(
            data_set_id=dataset.id,
            fm_meta_data_id=feature_model_metadata.id,
        )

        # associated authors in feature model
        for idx, author_name in enumerate(
            uploaded_models_data.get(f"author_name_{uvl_identifier}", [])
        ):
            AuthorRepository().create(
                name=author_name,
                affiliation=uploaded_models_data[
                    f"author_affiliation_{uvl_identifier}"
                ][idx],
                orcid=uploaded_models_data[f"author_orcid_{uvl_identifier}"][idx],
                fm_meta_data_id=feature_model_metadata.id,
            )

        # associated files in feature model
        user_id = current_user.id
        file_path = os.path.join(
            app.upload_folder_name(), "temp", str(user_id), uvl_filename
        )
        checksum, size = calculate_checksum_and_size(file_path)

        FileRepository().create(
            name=uvl_filename,
            checksum=checksum,
            size=size,
            feature_model_id=feature_model.id,
        )

        feature_models.append(feature_model)

    return feature_models


def calculate_checksum_and_size(file_path):
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as file:
        content = file.read()
        hash_md5 = hashlib.md5(content).hexdigest()
        return hash_md5, file_size


def move_feature_models(dataset_id, feature_models, user=None):
    user_id = current_user.id if user is None else user.id
    source_dir = f"uploads/temp/{user_id}/"
    dest_dir = f"uploads/user_{user_id}/dataset_{dataset_id}/"

    os.makedirs(dest_dir, exist_ok=True)

    for feature_model in feature_models:
        uvl_filename = feature_model.fm_meta_data.uvl_filename
        shutil.move(os.path.join(source_dir, uvl_filename), dest_dir)


@dataset_bp.route("/dataset/file/upload", methods=["POST"])
@login_required
def upload():
    file = request.files["file"]
    user_id = current_user.id
    temp_folder = os.path.join(app.upload_folder_name(), "temp", str(user_id))

    if not file or not file.filename.endswith(".uvl"):
        return jsonify({"message": "No valid file"}), 400

    # create temp folder
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    file_path = os.path.join(temp_folder, file.filename)

    if os.path.exists(file_path):
        # Generate unique filename (by recursion)
        base_name, extension = os.path.splitext(file.filename)
        i = 1
        while os.path.exists(
            os.path.join(temp_folder, f"{base_name} ({i}){extension}")
        ):
            i += 1
        new_filename = f"{base_name} ({i}){extension}"
        file_path = os.path.join(temp_folder, new_filename)
    else:
        new_filename = file.filename

    try:
        file.save(file_path)
        if True:
            return (
                jsonify(
                    {
                        "message": "UVL uploaded and validated successfully",
                        "filename": new_filename,
                    }
                ),
                200,
            )
        else:
            return jsonify({"message": "No valid model"}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@dataset_bp.route("/dataset/file/delete", methods=["POST"])
def delete():
    data = request.get_json()
    filename = data.get("file")
    user_id = current_user.id
    temp_folder = os.path.join(app.upload_folder_name(), "temp", str(user_id))
    filepath = os.path.join(temp_folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": "File deleted successfully"})

    return jsonify({"error": "Error: File not found"})


@dataset_bp.route("/dataset/download/<int:dataset_id>", methods=["GET"])
def download_dataset(dataset_id):
    dataset = DataSetRepository().get_or_404(dataset_id)

    file_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"dataset_{dataset_id}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for subdir, dirs, files in os.walk(file_path):
            for file in files:
                full_path = os.path.join(subdir, file)

                relative_path = os.path.relpath(full_path, file_path)

                zipf.write(
                    full_path,
                    arcname=os.path.join(
                        os.path.basename(zip_path[:-4]), relative_path
                    ),
                )

    user_cookie = request.cookies.get("download_cookie")
    if not user_cookie:
        user_cookie = str(
            uuid.uuid4()
        )  # Generate a new unique identifier if it does not exist
        # Save the cookie to the user's browser
        resp = make_response(
            send_from_directory(
                temp_dir,
                f"dataset_{dataset_id}.zip",
                as_attachment=True,
                mimetype="application/zip",
            )
        )
        resp.set_cookie("download_cookie", user_cookie)
    else:
        resp = send_from_directory(
            temp_dir,
            f"dataset_{dataset_id}.zip",
            as_attachment=True,
            mimetype="application/zip",
        )

    # Record the download in your database
    DSDownloadRecordRepository().create(
        user_id=current_user.id if current_user.is_authenticated else None,
        dataset_id=dataset_id,
        download_date=datetime.utcnow(),
        download_cookie=user_cookie,
    )

    return resp


@dataset_bp.route("/dataset/view/<int:dataset_id>", methods=["GET"])
def view_dataset(dataset_id):
    dataset = DataSetRepository().get_or_404(dataset_id)

    # Get the cookie from the request or generate a new one if it does not exist
    user_cookie = request.cookies.get("view_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())

    # Record the view in your database
    DSViewRecordRepository().create(
        user_id=current_user.id if current_user.is_authenticated else None,
        dataset_id=dataset_id,
        view_date=datetime.utcnow(),
        view_cookie=user_cookie,
    )

    # Save the cookie to the user's browser
    resp = make_response(render_template("dataset/view_dataset.html", dataset=dataset))
    resp.set_cookie("view_cookie", user_cookie)

    return resp


@dataset_bp.route("/file/download/<int:file_id>", methods=["GET"])
def download_file(file_id):
    file = FileRepository().get_or_404(file_id)
    filename = file.name

    directory_path = f"uploads/user_{file.feature_model.data_set.user_id}/dataset_{file.feature_model.data_set_id}/"
    parent_directory_path = os.path.dirname(current_app.root_path)
    file_path = os.path.join(parent_directory_path, directory_path)

    # Get the cookie from the request or generate a new one if it does not exist
    user_cookie = request.cookies.get("file_download_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())

    # Record the download in your database
    FileDownloadRecordRepository().create(
        user_id=current_user.id if current_user.is_authenticated else None,
        file_id=file_id,
        download_date=datetime.utcnow(),
        download_cookie=user_cookie,
    )

    # Save the cookie to the user's browser
    resp = make_response(
        send_from_directory(directory=file_path, path=filename, as_attachment=True)
    )
    resp.set_cookie("file_download_cookie", user_cookie)

    return resp


@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):
    # Busca el dataset por DOI
    ds_meta_data = DSMetaDataRepository().filter_by_doi(doi)
    if not ds_meta_data:
        abort(404)

    dataset = ds_meta_data.data_set
    if dataset:
        dataset_id = dataset.id
        user_cookie = request.cookies.get("view_cookie", str(uuid.uuid4()))

        # Registra la vista del dataset
        DSViewRecordRepository().create(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset_id,
            view_date=datetime.utcnow(),
            view_cookie=user_cookie,
        )

        # Prepara la respuesta y establece la cookie
        resp = make_response(
            render_template("dataset/view_dataset.html", dataset=dataset)
        )
        resp.set_cookie(
            "view_cookie", user_cookie, max_age=30 * 24 * 60 * 60
        )  # Ejemplo: cookie expira en 30 días

        return resp
    else:
        # Aquí puedes manejar el caso de que el DOI no corresponda a un dataset existente
        # Por ejemplo, mostrar un error 404 o redirigir a una página de error
        return "Dataset no encontrado", 404
