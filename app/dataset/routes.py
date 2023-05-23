import os

from flask import flash, redirect, render_template, url_for, request, jsonify
from flask_login import login_required, current_user

import app
from .forms import DataSetForm
from .models import DataSet, DSMetrics, FeatureModel, File, FMMetaData, FMMetrics, DSMetaData, Author
from . import dataset_bp


@dataset_bp.route('/dataset/upload', methods=['GET', 'POST'])
@login_required
def create_dataset():
    form = DataSetForm()
    if form.validate_on_submit():
        dataset = DataSet(user_id=form.user_id.data, meta_data_id=form.meta_data_id.data)
        app.db.session.add(dataset)
        app.db.session.commit()
        flash('Your DataSet has been created!')
        return redirect(url_for('index'))
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