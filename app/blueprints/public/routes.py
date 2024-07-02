import logging

from flask import render_template
from flask_login import login_required

from app.blueprints.public import public_bp
from app.blueprints.dataset.services import DataSetService

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    logger.info("Access index")
    dataset_service = DataSetService()

    return render_template(
        "public/index.html",
        datasets=dataset_service.latest_synchronized(),
        datasets_counter=dataset_service.count(),
        feature_models_counter=dataset_service.count_feature_models(),
    )


@public_bp.route("/secret")
@login_required
def secret():
    return "Esto es secreto!"
