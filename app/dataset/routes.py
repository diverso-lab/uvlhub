from flask import flash, redirect, render_template, url_for

import app
from .forms import DataSetForm
from .models import DataSet, DSMetrics, FeatureModel, File, FMMetaData, FMMetrics, DSMetaData, Author
from . import dataset_bp


@dataset_bp.route('/dataset/create', methods=['GET', 'POST'])
def create_dataset():
    form = DataSetForm()
    if form.validate_on_submit():
        dataset = DataSet(user_id=form.user_id.data, meta_data_id=form.meta_data_id.data)
        app.db.session.add(dataset)
        app.db.session.commit()
        flash('Your DataSet has been created!')
        return redirect(url_for('index'))
    return render_template('dataset/create_dataset.html', title='Create DataSet', form=form)
