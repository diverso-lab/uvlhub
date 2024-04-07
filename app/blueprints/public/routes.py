import logging

from flask_login import login_required

import app

from flask import render_template
from app.blueprints.public import public_bp
from ..dataset.models import DataSet, DSMetaData

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    logger.info('Access index')

    latest_datasets = DataSet.query.join(DSMetaData).filter(
        DSMetaData.dataset_doi.isnot(None)
    ).order_by(DataSet.created_at.desc()).limit(5).all()

    datasets_counter = app.datasets_counter()
    feature_models_counter = app.feature_models_counter()

    return render_template("public/index.html",
                           datasets=latest_datasets,
                           datasets_counter=datasets_counter,
                           feature_models_counter=feature_models_counter)


@public_bp.route('/secret')
@login_required
def secret():
    return "Esto es secreto!"
