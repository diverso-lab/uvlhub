from flask import render_template

from app.features.team import team_bp


@team_bp.route("/team", methods=["GET"])
def index():
    return render_template("team/index.html")
