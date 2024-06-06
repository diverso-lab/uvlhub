import logging

from flask import render_template
from flask_login import login_required

from app.blueprints.public import public_bp
from app.blueprints.dataset.repositories import DataSetRepository, FeatureModelRepository

logger = logging.getLogger(__name__)
dataset_repository = DataSetRepository()


@public_bp.route("/")
def index():
    logger.info("Access index")

    return render_template(
        "public/index.html",
        datasets=dataset_repository.latest_synchronized(),
        datasets_counter=dataset_repository.count(),
        feature_models_counter=FeatureModelRepository().count(),
    )


@public_bp.route("/secret")
@login_required
def secret():
    return "Esto es secreto!"
