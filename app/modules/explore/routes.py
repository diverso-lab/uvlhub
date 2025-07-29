from flask import render_template, request, jsonify

from app.modules.dataset.models import PublicationType
from app.modules.elasticsearch.services import ElasticsearchService
from app.modules.explore import explore_bp

search_service = ElasticsearchService()

@explore_bp.route("/explore", methods=["GET", "POST"])
def index():
    publication_type_choices = [(pt.value, pt.name.replace("_", " ").title()) for pt in PublicationType]
    return render_template("explore/index.html", publication_type_choices=publication_type_choices)

@explore_bp.route("/search")
def search():
    query = request.args.get("q", "")
    try:
        results = search_service.search(query, size=10)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@explore_bp.route("/api/v1/search")
def api_search():
    query = request.args.get("q", "")
    publication_type = request.args.get("publication_type")
    sorting = request.args.get("sorting", "newest")

    results = search_service.search(
        query=query,
        publication_type=publication_type,
        sorting=sorting
    )

    return jsonify(results)
