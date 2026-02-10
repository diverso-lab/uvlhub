from flask import current_app, flash, redirect, url_for
from flask_login import login_user

from app.modules.orcid import orcid_bp
from app.modules.orcid.services import OrcidService


@orcid_bp.before_app_request
def before_request():
    # If you keep this pattern for now, at least guarantee the service exists.
    # Consider moving OAuth client initialization to app factory later.
    current_app.orcid_service = OrcidService()


@orcid_bp.route("/orcid/login")
def login():
    redirect_uri = url_for("orcid.authorize", _external=True, _scheme="https")

    try:
        return current_app.orcid_service.orcid_client.authorize_redirect(redirect_uri)
    except Exception as exc:
        current_app.logger.exception("ORCID authorize_redirect failed: %s", exc)
        flash("ORCID login failed. Please try again.", "danger")
        return redirect(url_for("auth.login"))  # adjust to your login route


@orcid_bp.route("/orcid/authorize")
def authorize():
    try:
        token = current_app.orcid_service.orcid_client.authorize_access_token()
    except Exception as exc:
        # Covers state mismatch, missing session, provider errors, etc.
        current_app.logger.exception("ORCID authorize_access_token failed: %s", exc)
        flash("ORCID authorization failed (invalid session or provider error). Please try again.", "danger")
        return redirect(url_for("auth.login"))

    user_info, err = current_app.orcid_service.get_orcid_user_info(token)
    if err:
        flash(err, "danger")
        return redirect(url_for("auth.login"))

    user, err = current_app.orcid_service.get_or_create_user(user_info)
    if err:
        flash(err, "danger")
        return redirect(url_for("auth.login"))

    login_user(user)
    flash("Signed in with ORCID.", "success")
    return redirect(url_for("public.index"))  # adjust to your home route
