import os
import json
import hashlib

from flask import flash, redirect, render_template, url_for, request, jsonify
from flask_login import login_required, current_user

import app
from .forms import DataSetForm
from .models import DataSet, DSMetrics, FeatureModel, File, FMMetaData, FMMetrics, DSMetaData, Author, PublicationType
from . import dataset_bp
from ..zenodo import create_new_deposition, test_zenodo_connection


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
            zenodo_response_json = create_new_deposition(dataset)

            response_data = json.dumps(zenodo_response_json)
            data = json.loads(response_data)
            if data.get('conceptrecid'):

                # create feature models
                feature_models = create_feature_models_in_db(dataset, uploaded_models_data)

                # TODO: Send feature models to Zenodo

            return jsonify({'message': zenodo_response_json}), 200

        except Exception as e:
            return jsonify({'message': str(e)}), 500

    return render_template('dataset/upload_dataset.html', title='Create DataSet', form=form)


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
            author_gnd = basic_info_data["author_gnd"][i]

            author = Author(
                name=author_name,
                affiliation=author_affiliation,
                orcid=author_orcid,
                gnd=author_gnd,
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

            # create feature model metadata
            feature_model_metadata = FMMetaData(
                title=title,
                description=description,
                publication_type=PublicationType(uvl_publication_type),
                publication_doi=publication_doi,
                tags=tags
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
                        gnd=uploaded_models_data[f"author_gnd_{uvl_identifier}"][a],
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


@dataset_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    file = request.files['file']
    user_id = current_user.id
    temp_folder = os.path.join(app.upload_folder_name(), 'temp', str(user_id))

    if file and file.filename.endswith('.uvl'):
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        file.save(os.path.join(temp_folder, file.filename))
        return jsonify({'message': 'File uploaded successfully'})
    else:
        return jsonify({'error': 'Error: No valid file'})


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
