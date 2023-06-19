import io
import logging
import os
import json
import hashlib
import shutil
import tempfile
from typing import List
from zipfile import ZipFile

from flask import flash, redirect, render_template, url_for, request, jsonify, send_file, send_from_directory, abort, \
    current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

import app
from .forms import DataSetForm
from .models import DataSet, DSMetrics, FeatureModel, File, FMMetaData, FMMetrics, DSMetaData, Author, PublicationType
from . import dataset_bp
from ..auth.models import User
from ..flama import flamapy_valid_model
from ..zenodo import zenodo_create_new_deposition, test_zenodo_connection, zenodo_upload_file, \
    zenodo_publish_deposition, zenodo_get_doi, test_full_zenodo_connection


@dataset_bp.route('/zenodo/test', methods=['GET'])
def zenodo_test() -> dict:
    return test_full_zenodo_connection()


@dataset_bp.route('/dataset/upload', methods=['GET', 'POST'])
@login_required
def create_dataset():
    form = DataSetForm()
    if request.method == 'POST':

        try:

            # get JSON from frontend
            form_data_json = request.form.get('formData')
            form_data_dict = json.loads(form_data_json)

            # get dicts
            basic_info_data = form_data_dict["basic_info_form"]
            uploaded_models_data = form_data_dict["uploaded_models_form"]

            # create dataset
            dataset = create_dataset_in_db(basic_info_data)

            # send dataset as deposition to Zenodo
            zenodo_response_json = zenodo_create_new_deposition(dataset)

            response_data = json.dumps(zenodo_response_json)
            data = json.loads(response_data)
            if data.get('conceptrecid'):

                deposition_id = data.get('id')

                # update dataset with deposition id in Zenodo
                dataset.ds_meta_data.deposition_id = deposition_id
                app.db.session.commit()

                # create feature models
                feature_models = create_feature_models_in_db(dataset, uploaded_models_data)

                try:
                    # iterate for each feature model (one feature model = one request to Zenodo
                    for feature_model in feature_models:
                        zenodo_upload_file(deposition_id, feature_model)

                    # publish deposition
                    zenodo_publish_deposition(deposition_id)

                    # update DOI
                    deposition_doi = zenodo_get_doi(deposition_id)
                    dataset.ds_meta_data.dataset_doi = deposition_doi
                    app.db.session.commit()
                except Exception as e:
                    pass

                # move feature models permanently
                move_feature_models(dataset.id, feature_models)

            else:
                # it has not been possible to create the deposition in Zenodo, so we save everything locally

                # create feature models
                feature_models = create_feature_models_in_db(dataset, uploaded_models_data)

                # move feature models permanently
                move_feature_models(dataset.id, feature_models)
                pass

            return jsonify({'message': zenodo_response_json}), 200

        except Exception as e:
            return jsonify({'message': str(e)}), 500

    return render_template('dataset/upload_dataset.html', form=form)


@dataset_bp.route('/dataset/list', methods=['GET', 'POST'])
@login_required
def list_dataset():
    # synchronized datasets
    datasets = DataSet.query.join(DSMetaData).filter(
        DataSet.user_id == current_user.id,
        DSMetaData.dataset_doi.isnot(None)
    ).order_by(DataSet.created_at.desc()).all()

    # local datasets
    local_datasets = DataSet.query.join(DSMetaData).filter(
        DataSet.user_id == current_user.id,
        DSMetaData.dataset_doi.is_(None)
    ).order_by(DataSet.created_at.desc()).all()

    return render_template('dataset/list_datasets.html', datasets=datasets, local_datasets=local_datasets)


def create_dataset_in_db(basic_info_data):
    # get dataset metadata
    title = basic_info_data["title"][0]
    description = basic_info_data["description"][0]
    publication_type = basic_info_data["publication_type"][0]
    publication_doi = basic_info_data["publication_doi"][0]
    tags = basic_info_data["tags"][0]

    # create dataset metadata
    ds_meta_data = DSMetaData(
        title=title,
        description=description,
        publication_type=PublicationType(publication_type),
        publication_doi=publication_doi,
        tags=tags
    )
    app.db.session.add(ds_meta_data)
    app.db.session.commit()

    # create dataset metadata authors
    # how many authors are there?
    if "author_name" in basic_info_data:
        number_of_authors = len(basic_info_data["author_name"])
        for i in range(number_of_authors):
            author_name = basic_info_data["author_name"][i]
            author_affiliation = basic_info_data["author_affiliation"][i]
            author_orcid = basic_info_data["author_orcid"][i]

            author = Author(
                name=author_name,
                affiliation=author_affiliation,
                orcid=author_orcid,
                ds_meta_data_id=ds_meta_data.id
            )
            app.db.session.add(author)
            app.db.session.commit()
    else:
        author = Author(
            name=current_user.name,
            affiliation='',  # TODO: Add affiliation and ORCID to user profile
            ds_meta_data_id=ds_meta_data.id
        )
        app.db.session.add(author)
        app.db.session.commit()

    # create dataset
    dataset = DataSet(user_id=current_user.id, ds_meta_data_id=ds_meta_data.id)
    app.db.session.add(dataset)
    app.db.session.commit()

    return dataset


def create_feature_models_in_db(dataset: DataSet, uploaded_models_data: dict):
    feature_models = []

    if "uvl_identifier" in uploaded_models_data:

        number_of_models = len(uploaded_models_data["uvl_identifier"])

        for i in range(number_of_models):

            # get feature model metadata
            uvl_identifier = uploaded_models_data["uvl_identifier"][i]
            uvl_filename = uploaded_models_data["uvl_filename"][i]
            title = uploaded_models_data["title"][i]
            description = uploaded_models_data["description"][i]
            uvl_publication_type = uploaded_models_data["uvl_publication_type"][i]
            publication_doi = uploaded_models_data["publication_doi"][i]
            tags = uploaded_models_data["tags"][i]
            uvl_version = uploaded_models_data["uvl_version"][i]

            # create feature model metadata
            feature_model_metadata = FMMetaData(
                uvl_filename=uvl_filename,
                title=title,
                description=description,
                publication_type=PublicationType(uvl_publication_type),
                publication_doi=publication_doi,
                tags=tags,
                uvl_version=uvl_version
            )
            app.db.session.add(feature_model_metadata)
            app.db.session.commit()

            # create feature model
            feature_model = FeatureModel(
                data_set_id=dataset.id,
                fm_meta_data_id=feature_model_metadata.id
            )
            app.db.session.add(feature_model)
            app.db.session.commit()

            # associated authors in feature model
            if f"author_name_{uvl_identifier}" in uploaded_models_data.keys():
                number_of_authors_in_model = len(uploaded_models_data[f"author_name_{uvl_identifier}"])
                for a in range(number_of_authors_in_model):
                    author = Author(
                        name=uploaded_models_data[f"author_name_{uvl_identifier}"][a],
                        affiliation=uploaded_models_data[f"author_affiliation_{uvl_identifier}"][a],
                        orcid=uploaded_models_data[f"author_orcid_{uvl_identifier}"][a],
                        fm_meta_data_id=feature_model_metadata.id
                    )
                    app.db.session.add(author)
                    app.db.session.commit()

            # associated files in feature model
            user_id = current_user.id
            file_path = os.path.join(app.upload_folder_name(), 'temp', str(user_id), uvl_filename)
            checksum, size = calculate_checksum_and_size(file_path)
            file = File(
                name=uvl_filename,
                checksum=checksum,
                size=size,
                feature_model_id=feature_model.id
            )
            app.db.session.add(file)
            app.db.session.commit()

            feature_models.append(feature_model)

    return feature_models


def calculate_checksum_and_size(file_path):
    file_size = os.path.getsize(file_path)
    with open(file_path, 'rb') as file:
        content = file.read()
        hash_md5 = hashlib.md5(content).hexdigest()
        return hash_md5, file_size


def move_feature_models(dataset_id, feature_models,user=None):
    user_id = current_user.id if user is None else user.id
    source_dir = f'uploads/temp/{user_id}/'
    dest_dir = f'uploads/user_{user_id}/dataset_{dataset_id}/'

    os.makedirs(dest_dir, exist_ok=True)

    for feature_model in feature_models:
        uvl_filename = feature_model.fm_meta_data.uvl_filename
        shutil.move(os.path.join(source_dir, uvl_filename), dest_dir)


@dataset_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    file = request.files['file']
    user_id = current_user.id
    temp_folder = os.path.join(app.upload_folder_name(), 'temp', str(user_id))

    if file and file.filename.endswith('.uvl'):
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        try:
            file.save(os.path.join(temp_folder, file.filename))
            valid_model = flamapy_valid_model(uvl_filename=file.filename)
            if valid_model:
                return jsonify({'message': 'UVL uploaded and validated successfully'}), 200
            else:
                return jsonify({'message': 'No valid model'}), 400
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    else:
        return jsonify({'message': 'No valid file'}), 400


@dataset_bp.route('/delete', methods=['POST'])
def delete():
    data = request.get_json()
    filename = data.get('file')
    user_id = current_user.id
    temp_folder = os.path.join(app.upload_folder_name(), 'temp', str(user_id))
    filepath = os.path.join(temp_folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'message': 'File deleted successfully'})
    else:
        return jsonify({'error': 'Error: File not found'})


@dataset_bp.route('/dataset/download/<int:dataset_id>', methods=['GET'])
def download_dataset(dataset_id):
    dataset = DataSet.query.get(dataset_id)
    if dataset is None:
        return "Dataset not found", 404

    file_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f'dataset_{dataset_id}.zip')

    with ZipFile(zip_path, 'w') as zipf:
        for subdir, dirs, files in os.walk(file_path):
            for file in files:
                full_path = os.path.join(subdir, file)

                relative_path = os.path.relpath(full_path, file_path)

                zipf.write(full_path, arcname=os.path.join(os.path.basename(zip_path[:-4]), relative_path))

    return send_from_directory(
        temp_dir,
        f'dataset_{dataset_id}.zip',
        as_attachment=True,
        mimetype='application/zip'
    )


@dataset_bp.route('/dataset/view/<int:dataset_id>', methods=['GET'])
def view_dataset(dataset_id):
    dataset = DataSet.query.get_or_404(dataset_id)
    return render_template('dataset/view_dataset.html', dataset=dataset)


@dataset_bp.route('/file/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    file = File.query.get_or_404(file_id)
    filename = file.name

    directory_path = f"uploads/user_{file.feature_model.data_set.user_id}/dataset_{file.feature_model.data_set_id}/"
    parent_directory_path = os.path.dirname(current_app.root_path)
    file_path = os.path.join(parent_directory_path, directory_path)

    return send_from_directory(directory=file_path, path=filename, as_attachment=True)


'''
    API ENDPOINTS FOR DATASET MODEL
'''


@dataset_bp.route('/api/v1/dataset/', methods=['GET'])
def get_all_dataset():
    datasets = DataSet.query.order_by(DataSet.created_at.desc()).all()
    dataset_list = [dataset.to_dict() for dataset in datasets]
    return jsonify(dataset_list)


@dataset_bp.route('/api/v1/dataset/<int:dataset_id>', methods=['GET'])
def get_dataset(dataset_id):
    dataset = DataSet.query.get_or_404(dataset_id)
    return dataset.to_dict()


@dataset_bp.route('/api/v1/dataset/', methods=['POST'])
def api_create_dataset():
    """
    PART 1: GET DATA
    """

    user = app.get_user_by_token("BLABLABLA")  # TODO
    data = json.loads(request.files['json'].read())
    temp_folder = os.path.join(app.upload_folder_name(), 'temp', str(user.id))

    info = data['info']
    models = data['models']

    """
    PART 2: CREATE BASIC DATA
    """
    ds_meta_data = _create_ds_meta_data(info=info)
    authors = _create_authors(info=info, ds_meta_data=ds_meta_data)
    dataset = _create_dataset(user=user, ds_meta_data=ds_meta_data)

    """
    PART 3: SEND BASIC DATA TO ZENODO
    """
    zenodo_response_json = zenodo_create_new_deposition(dataset)
    response_data = json.dumps(zenodo_response_json)
    zenodo_json_data = json.loads(response_data)

    """
    PART 4: SAVE FILES IN TEMP FOLDER
    """
    files = request.files.to_dict()
    for filename, file in files.items():
        if filename != 'json':

            if file and filename.endswith('.uvl'):

                # create temporal folder for this user
                if not os.path.exists(temp_folder):
                    os.makedirs(temp_folder)

                try:
                    file.save(os.path.join(temp_folder, filename))
                    # TODO: Change valid model function
                    valid_model = flamapy_valid_model(uvl_filename=filename, user=user)
                    if valid_model:
                        continue
                    else:
                        return jsonify({'message': f'{filename} is not a valid model'}), 400
                except Exception as e:
                    return jsonify({'exception': str(e)}), 500

            else:
                return jsonify({'message': f'{filename} is not a valid extension'}), 400

    """
    PART 5: CREATE FEATURE MODELS
    """
    feature_models = _create_feature_models(dataset=dataset, models=models, user=user)

    if zenodo_json_data.get('conceptrecid'):

        # update dataset with deposition id in Zenodo
        deposition_id = zenodo_json_data.get('id')
        dataset.ds_meta_data.deposition_id = deposition_id
        app.db.session.commit()

        """
        PART 6: SEND FILES TO ZENODO AND PUBLISH
        """
        try:
            # iterate for each feature model (one feature model = one request to Zenodo
            for feature_model in feature_models:
                zenodo_upload_file(deposition_id, feature_model, user=user)

            # publish deposition
            zenodo_publish_deposition(deposition_id)

            # update DOI
            deposition_doi = zenodo_get_doi(deposition_id)
            dataset.ds_meta_data.dataset_doi = deposition_doi
            app.db.session.commit()
        except Exception as e:
            return jsonify({'exception': str(e)}), 500

    """
    PART 7: MOVE FEATURE MODELS PERMANENTLY
    """
    move_feature_models(dataset.id, feature_models, user=user)

    return jsonify({'message': 'Everything works fine!'}), 200


def _create_ds_meta_data(info: dict) -> DSMetaData:
    ds_meta_data = DSMetaData(
        title=info["title"],
        description=info["description"],
        publication_type=PublicationType(info["publication_type"]),
        publication_doi=info["publication_doi"],
        tags=','.join(tag.strip() for tag in info['tags'])
    )
    app.db.session.add(ds_meta_data)
    app.db.session.commit()

    return ds_meta_data


def _create_authors(info: dict, ds_meta_data: DSMetaData) -> List[Author]:
    authors = []

    authors_info = info.get("authors")
    if authors_info:
        for author_info in authors_info:
            author = Author(
                name=author_info.get("name"),
                affiliation=author_info.get("affiliation"),
                orcid=author_info.get("orcid", None),
                ds_meta_data_id=ds_meta_data.id
            )
            authors.append(author)
            app.db.session.add(author)

        app.db.session.commit()

    return authors


def _create_dataset(user: User, ds_meta_data: DSMetaData) -> DataSet:
    dataset = DataSet(user_id=user.id, ds_meta_data_id=ds_meta_data.id)
    app.db.session.add(dataset)
    app.db.session.commit()

    return dataset


def _create_feature_models(dataset: DataSet, models: dict, user: User) -> List[FeatureModel]:
    feature_models = []

    for model in models:

        filename = model['filename']
        title = model['title']
        description = model['description']
        publication_type = model['publication_type']
        publication_doi = model['publication_doi']
        tags = ','.join(tag.strip() for tag in model['tags'])

        # create feature model metadata
        feature_model_metadata = FMMetaData(
            uvl_filename=filename,
            title=title,
            description=description,
            publication_type=publication_type,
            publication_doi=publication_doi,
            tags=tags
        )
        app.db.session.add(feature_model_metadata)
        app.db.session.commit()

        # associated authors in feature model
        for author_data in model['authors']:
            author = Author(
                name=author_data['name'],
                affiliation=author_data['affiliation'],
                fm_meta_data_id=feature_model_metadata.id
            )
            app.db.session.add(author)
            app.db.session.commit()

        # create feature model
        feature_model = FeatureModel(
            data_set_id=dataset.id,
            fm_meta_data_id=feature_model_metadata.id
        )
        app.db.session.add(feature_model)
        app.db.session.commit()

        # associated files in feature model
        user_id = user.id
        file_path = os.path.join(app.upload_folder_name(), 'temp', str(user_id), model['filename'])
        checksum, size = calculate_checksum_and_size(file_path)
        file = File(
            name=model['filename'],
            checksum=checksum,
            size=size,
            feature_model_id=feature_model.id
        )
        app.db.session.add(file)
        app.db.session.commit()

        feature_models.append(feature_model)

    return feature_models
