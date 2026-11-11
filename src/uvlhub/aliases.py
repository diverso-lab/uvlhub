"""Old uvlhub addresses the product answers on behalf of the features.

uvlhub.io 2.12 served these and clients outside the hub still call them
(frozen_urls.toml). The redirects here are temporary: the legacy_urls
feature (CO-2) takes them over with its alias table, its deprecation dates
and its counters, and then this module goes.
"""

from flask import Blueprint, redirect, url_for

aliases_bp = Blueprint("uvlhub_aliases", __name__)


@aliases_bp.route("/api/me", methods=["GET"])
def api_me():
    """The signed-in user's profile, which the authors' JavaScript asked for
    at /api/me. profile serves it at /api/v1/profile/me, and a 308 keeps the
    method on the way there."""
    return redirect(url_for("profile.my_profile"), code=308)
