import logging

from flask_login import login_required

import app

from flask import render_template
from app.blueprints.public import public_bp
from ..dataset.models import DataSet, DSMetaData, DSDownloadRecord, DSViewRecord, FileDownloadRecord, FileViewRecord

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    logger.info('Access index')

    latest_datasets = DataSet.query.join(DSMetaData).filter(
        DSMetaData.dataset_doi.isnot(None)
    ).order_by(DataSet.created_at.desc()).limit(5).all()

    datasets_counter = app.datasets_counter()
    feature_models_counter = app.feature_models_counter()

    # Downloads
    total_dataset_downloads = DSDownloadRecord.query.count()
    total_feature_model_downloads = FileDownloadRecord.query.count()

    # Views
    total_dataset_views = DSViewRecord.query.count()
    total_feature_model_views = FileViewRecord.query.count()

    return render_template("public/index.html",
                           datasets=latest_datasets,
                           datasets_counter=datasets_counter,
                           feature_models_counter=feature_models_counter,
                           total_dataset_downloads=total_dataset_downloads,
                           total_feature_model_downloads=total_feature_model_downloads,
                           total_dataset_views=total_dataset_views,
                           total_feature_model_views=total_feature_model_views)


@public_bp.route('/secret')
@login_required
def secret():
    return "Esto es secreto!"
    
