from flask import render_template

from app.modules.statistics import statistics_bp
from app.modules.statistics.services import DashboardService


@statistics_bp.route("/statistics", methods=["GET"])
def index():
    dashboard = DashboardService().build_dashboard()
    return render_template("statistics/index.html", dashboard=dashboard)
