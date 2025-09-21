from flask import jsonify, render_template, request

from app.modules.dataset.models import PublicationType
from app.modules.explore import explore_bp


@explore_bp.route("/explore", methods=["GET", "POST"])
def index():
    # value = se usa en el filtro (Enum.value) → ej: "conferencepaper"
    # label = se muestra en el select (bonito) → ej: "Conference Paper"
    publication_type_choices = [(pt.value, pt.name.replace("_", " ").title()) for pt in PublicationType]
    return render_template(
        "explore/index.html",
        publication_type_choices=publication_type_choices,
    )


@explore_bp.route("/search")
def search():
    """Legacy endpoint (mantener si hay dependencias en front viejo)."""
    from app.modules.elasticsearch.services import ElasticsearchService

    search_service = ElasticsearchService()

    query = request.args.get("q", "")
    try:
        results = search_service.search(query=query, size=10)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@explore_bp.route("/api/v1/search")
def api_search():
    from app.modules.elasticsearch.services import ElasticsearchService

    search_service = ElasticsearchService()

    query = request.args.get("q", "")
    publication_type = request.args.get("publication_type")
    sorting = request.args.get("sorting", "newest")
    tags = request.args.get("tags")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 10))

    tags_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    results, total = search_service.search(
        query=query,
        publication_type=publication_type,
        sorting=sorting,
        tags=tags_list,
        date_from=date_from,
        date_to=date_to,
        page=page,
        size=size,
    )

    return jsonify({"results": results, "total": total, "page": page, "size": size})
