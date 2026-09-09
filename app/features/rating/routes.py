from flask import jsonify, request
from flask_login import current_user, login_required

from app.features.dataset.services import DataSetService
from app.features.rating import rating_bp
from app.features.rating.services import RatingService

dataset_service = DataSetService()
rating_service = RatingService()


def _ratable_or_error(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)
    if not dataset.ds_meta_data or not dataset.ds_meta_data.dataset_doi:
        return None, (jsonify({"error": "Only published datasets (with a DOI) can be rated."}), 403)
    return dataset, None


@rating_bp.route("/datasets/<int:dataset_id>/rating", methods=["GET"])
def get_rating(dataset_id):
    dataset, error = _ratable_or_error(dataset_id)
    if error:
        return error
    return jsonify(rating_service.get_state(dataset, current_user))


@rating_bp.route("/datasets/<int:dataset_id>/rating", methods=["POST"])
@login_required
def set_rating(dataset_id):
    dataset, error = _ratable_or_error(dataset_id)
    if error:
        return error

    payload = request.get_json(silent=True) or request.form
    vote = (payload.get("vote") or "").strip().lower()
    if vote not in {"like", "dislike", "none"}:
        return jsonify({"error": "vote must be 'like', 'dislike' or 'none'"}), 400

    return jsonify(rating_service.set_vote(dataset, current_user, vote))
