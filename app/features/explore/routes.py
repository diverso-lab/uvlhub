from flask import jsonify, render_template, request

from app.features.dataset.models import PublicationType
from app.features.explore import explore_bp


@explore_bp.route("/explore", methods=["GET", "POST"])
def index():
    # value -> used by the filter (Enum.value, e.g. "conferencepaper")
    # label -> shown in the select (pretty, e.g. "Conference Paper")
    publication_type_choices = [(pt.value, pt.name.replace("_", " ").title()) for pt in PublicationType]
    return render_template(
        "explore/index.html",
        publication_type_choices=publication_type_choices,
    )


@explore_bp.route("/search")
def search():
    """Legacy endpoint, kept for older front-end dependencies."""
    from app.features.elasticsearch.services import ElasticsearchService

    search_service = ElasticsearchService()

    query = request.args.get("q", "")
    try:
        results = search_service.search(query=query, size=10)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@explore_bp.route("/api/v1/search")
def api_search():
    from app.features.elasticsearch.services import ElasticsearchService

    search_service = ElasticsearchService()

    query = request.args.get("q", "")
    publication_type = request.args.get("publication_type")
    sorting = request.args.get("sorting", "newest")
    tags = request.args.get("tags")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    year = request.args.get("year")
    only_with_authors = request.args.get("only_with_authors")

    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 10))

    # Parse integer ranges - parse each individually
    def parse_int_or_none(value):
        if value:
            try:
                return int(value)
            except ValueError:
                return None
        return None

    features_min = parse_int_or_none(request.args.get("features_min"))
    features_max = parse_int_or_none(request.args.get("features_max"))
    models_min = parse_int_or_none(request.args.get("models_min"))
    models_max = parse_int_or_none(request.args.get("models_max"))
    size_min = parse_int_or_none(request.args.get("size_min"))
    size_max = parse_int_or_none(request.args.get("size_max"))
    files_min = parse_int_or_none(request.args.get("files_min"))
    files_max = parse_int_or_none(request.args.get("files_max"))

    if year:
        try:
            year = int(year)
        except ValueError:
            year = None

    only_with_authors = only_with_authors == 'true'

    tags_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    results, total = search_service.search(
        query=query,
        publication_type=publication_type,
        sorting=sorting,
        tags=tags_list,
        date_from=date_from,
        date_to=date_to,
        features_min=features_min,
        features_max=features_max,
        models_min=models_min,
        models_max=models_max,
        size_min=size_min,
        size_max=size_max,
        files_min=files_min,
        files_max=files_max,
        year=year,
        only_with_authors=only_with_authors,
        page=page,
        size=size,
    )

    return jsonify({"results": results, "total": total, "page": page, "size": size})
