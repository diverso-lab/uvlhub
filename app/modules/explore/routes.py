from flask import render_template, request, jsonify

from app.modules.elasticsearch.services import ElasticsearchService
from app.modules.explore import explore_bp
from app.modules.explore.forms import ExploreForm
from app.modules.explore.services import ExploreService

search_service = ElasticsearchService()

@explore_bp.route("/explore", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        query = request.args.get("query", "")
        form = ExploreForm()
        return render_template("explore/index.html", form=form, query=query)

    if request.method == "POST":
        criteria = request.get_json()
        datasets = ExploreService().filter(**criteria)
        return jsonify([dataset.to_dict() for dataset in datasets])

@explore_bp.route("/search")
def search():
    query = request.args.get("q", "")
    try:
        results = search_service.search(query, size=10)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
