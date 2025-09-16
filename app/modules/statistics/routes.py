from flask import render_template

from app.modules.statistics import statistics_bp


@statistics_bp.route("/statistics", methods=["GET"])
def index():
    return render_template("statistics/index.html")
