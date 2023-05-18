import logging

from flask import request, current_app, render_template

from . import public_bp

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    logger.info('Access index')
    return render_template("public/index.html")
