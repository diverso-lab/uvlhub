from flask import render_template

from app.features.featuremodel import featuremodel_bp


@featuremodel_bp.route("/featuremodel", methods=["GET"])
def index():
    return render_template("featuremodel/index.html")
