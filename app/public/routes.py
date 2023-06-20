import logging

from flask import request, current_app, render_template

from . import public_bp
from ..dataset.models import DataSet

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    logger.info('Access index')

    latest_datasets = DataSet.query.order_by(DataSet.created_at.desc()).limit(5).all()

    return render_template("public/index.html", datasets=latest_datasets)
