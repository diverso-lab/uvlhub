from splent_framework.blueprints.base_blueprint import BaseBlueprint

rating_bp = BaseBlueprint("rating", __name__, template_folder="templates")


def init_feature(app):
    """Expose the lineage like/dislike counts to any template."""
    from app.features.rating.services import RatingService

    def dataset_rating_counts(dataset):
        try:
            return RatingService().rating_counts(dataset)
        except Exception:
            return {"likes": 0, "dislikes": 0}

    app.add_template_global(dataset_rating_counts, name="dataset_rating_counts")
