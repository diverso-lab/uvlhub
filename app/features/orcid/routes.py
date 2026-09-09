from flask import current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user

from app.features.auth.services import AuthenticationService
from app.features.orcid import orcid_bp
from app.features.orcid.services import OrcidService

authentication_service = AuthenticationService()


@orcid_bp.before_app_request
def before_request():
    # Build the OAuth client once per process instead of on every request
    # (this hook is app-wide and would otherwise run for every static asset).
    # Moving it to the app factory is a future improvement.
    if not hasattr(current_app, "orcid_service"):
        current_app.orcid_service = OrcidService()


def _back_to_login(next_url):
    return redirect(url_for("auth.login", next=next_url) if next_url else url_for("auth.login"))


@orcid_bp.route("/orcid/login-email", methods=["GET", "POST"])
def login_email():
    next_url = authentication_service.get_safe_next_url()

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email:
            flash("Email is required.", "danger")
            return render_template("orcid/login_email.html", next_url=next_url)

        session["orcid_login_email"] = email
        if next_url:
            session["orcid_next_url"] = next_url
        return redirect(url_for("orcid.login"))

    return render_template("orcid/login_email.html", next_url=next_url)


@orcid_bp.route("/orcid/login")
def login():
    next_url = authentication_service.get_safe_next_url()
    if next_url:
        session["orcid_next_url"] = next_url
    else:
        session.pop("orcid_next_url", None)

    # The email entered at /orcid/login-email is the key that converges an ORCID
    # sign-in onto an existing account. When connecting ORCID to an account the
    # user is already in, we know who they are, so the step is not needed.
    if not session.get("orcid_connect_mode") and not session.get("orcid_login_email"):
        return redirect(url_for("orcid.login_email", next=next_url) if next_url else url_for("orcid.login_email"))

    redirect_uri = url_for("orcid.authorize", _external=True, _scheme="https")

    try:
        return current_app.orcid_service.orcid_client.authorize_redirect(redirect_uri)
    except Exception as exc:
        current_app.logger.exception("ORCID authorize_redirect failed: %s", exc)
        flash("ORCID login failed. Please try again.", "danger")
        return _back_to_login(next_url)


@orcid_bp.route("/orcid/authorize")
def authorize():
    from app.features.auth.repositories import ExternalIdentityRepository

    next_url = session.pop("orcid_next_url", None)
    if not authentication_service.is_safe_redirect_target(next_url):
        next_url = None

    connect_mode = session.pop("orcid_connect_mode", False)
    login_email = session.pop("orcid_login_email", None)
    connect_email = session.pop("orcid_connect_email", None)

    try:
        token = current_app.orcid_service.orcid_client.authorize_access_token()
    except Exception as exc:
        current_app.logger.exception("ORCID authorize_access_token failed: %s", exc)
        flash("ORCID authorization failed (invalid session or provider error). Please try again.", "danger")
        return _back_to_login(next_url)

    user_info, err = current_app.orcid_service.get_orcid_user_info(token)
    if err:
        flash(err, "danger")
        return _back_to_login(next_url)

    if connect_mode:
        if not current_user.is_authenticated:
            flash("You must be logged in to connect ORCID.", "danger")
            return redirect(url_for("auth.login"))

        _, err = current_app.orcid_service.link_identity(current_user, user_info, connect_email)
        if err:
            flash(err, "danger")
            return redirect(url_for("profile.edit_profile"))

        flash("ORCID account connected successfully", "success")
        return redirect(url_for("profile.edit_profile"))
    else:
        orcid_id = (user_info.get("sub") or "").strip()
        effective_email = (login_email or user_info.get("email") or "").strip().lower() or None

        # Without an email and with no prior ORCID link there is no safe way to
        # tell whether this person already has an account: send them back to the
        # email step rather than risk creating a duplicate.
        if not effective_email and not ExternalIdentityRepository().get_by_provider_id("orcid", orcid_id):
            flash("Please enter your email so we can find or create your account.", "danger")
            return redirect(url_for("orcid.login_email", next=next_url) if next_url else url_for("orcid.login_email"))

        user, err = current_app.orcid_service.get_or_create_user(user_info, effective_email)
        if err:
            flash(err, "danger")
            return _back_to_login(next_url)

        login_user(user)
        flash("Signed in with ORCID.", "success")
        return redirect(next_url or url_for("public.index"))
