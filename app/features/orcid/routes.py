from flask import current_app, flash, redirect, session, url_for
from flask_login import login_user

from app.features.auth.services import AuthenticationService
from app.features.orcid import orcid_bp
from app.features.orcid.services import OrcidService

authentication_service = AuthenticationService()


@orcid_bp.before_app_request
def before_request():
    # OAuth client is request-scoped for now; moving it to the app factory is a
    # future improvement, but creating it here keeps it always available.
    current_app.orcid_service = OrcidService()


def _back_to_login(next_url):
    return redirect(url_for("auth.login", next=next_url) if next_url else url_for("auth.login"))


@orcid_bp.route("/orcid/login")
def login():
    next_url = authentication_service.get_safe_next_url()
    if next_url:
        session["orcid_next_url"] = next_url
    else:
        session.pop("orcid_next_url", None)

    redirect_uri = url_for("orcid.authorize", _external=True, _scheme="https")

    try:
        return current_app.orcid_service.orcid_client.authorize_redirect(redirect_uri)
    except Exception as exc:
        current_app.logger.exception("ORCID authorize_redirect failed: %s", exc)
        flash("ORCID login failed. Please try again.", "danger")
        return _back_to_login(next_url)


@orcid_bp.route("/orcid/authorize")
def authorize():
    next_url = session.pop("orcid_next_url", None)
    if not authentication_service.is_safe_redirect_target(next_url):
        next_url = None

    try:
        token = current_app.orcid_service.orcid_client.authorize_access_token()
    except Exception as exc:
        # Covers state mismatch, missing session, provider errors, etc.
        current_app.logger.exception("ORCID authorize_access_token failed: %s", exc)
        flash("ORCID authorization failed (invalid session or provider error). Please try again.", "danger")
        return _back_to_login(next_url)

    user_info, err = current_app.orcid_service.get_orcid_user_info(token)
    if err:
        flash(err, "danger")
        return _back_to_login(next_url)

    user, err = current_app.orcid_service.get_or_create_user(user_info)
    if err:
        flash(err, "danger")
        return _back_to_login(next_url)

    login_user(user)
    flash("Signed in with ORCID.", "success")
    return redirect(next_url or url_for("public.index"))
