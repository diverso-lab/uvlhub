import os
import json

from flask import flash, redirect, render_template, url_for, request, jsonify
from flask_login import login_required, current_user

import app
from .forms import DataSetForm
from .models import DataSet, DSMetrics, FeatureModel, File, FMMetaData, FMMetrics, DSMetaData, Author, PublicationType
from . import dataset_bp


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



            dataset = DataSet(user_id=current_user.id, ds_meta_data_id=ds_meta_data.id)
            app.db.session.add(dataset)
            app.db.session.commit()

            return jsonify({'message': basic_info_data}), 200

        except Exception as e:
            return jsonify({'message': str(e)}), 500

    return render_template('dataset/upload_dataset.html', title='Create DataSet', form=form)


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
