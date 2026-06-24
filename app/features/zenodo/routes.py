from flask import render_template

from app.features.zenodo import zenodo_bp
from app.features.zenodo.services import ZenodoService


@zenodo_bp.route("/zenodo", methods=["GET"])
def index():
    return render_template("zenodo/index.html")


@zenodo_bp.route("/zenodo/test", methods=["GET"])
def zenodo_test() -> dict:
    service = ZenodoService()
    return service.test_full_connection()
