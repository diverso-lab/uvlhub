from flask import render_template

from app.modules.elasticsearch import elasticsearch_bp


@elasticsearch_bp.route("/elasticsearch", methods=["GET"])
def index():
    return render_template("elasticsearch/index.html")
