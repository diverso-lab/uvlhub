from flask import current_app, flash, redirect, session, url_for
from flask_login import current_user, login_user

from app.features.auth.services import AuthenticationService
from app.features.github import github_bp
from app.features.github.services import GithubService

authentication_service = AuthenticationService()


@github_bp.before_app_request
def before_request():
    if not hasattr(current_app, "github_service"):
        current_app.github_service = GithubService()


def _back_to_login(next_url):
    return redirect(url_for("auth.login", next=next_url) if next_url else url_for("auth.login"))


@github_bp.route("/github/login")
def login():
    next_url = authentication_service.get_safe_next_url()
    if next_url:
        session["github_next_url"] = next_url
    else:
        session.pop("github_next_url", None)

    redirect_uri = url_for("github.authorize", _external=True)

    try:
        return current_app.github_service.github_client.authorize_redirect(redirect_uri)
    except Exception as exc:
        current_app.logger.exception("GitHub authorize_redirect failed: %s", exc)
        flash("GitHub login failed. Please try again.", "danger")
        return _back_to_login(next_url)


@github_bp.route("/github/authorize")
def authorize():
    from app.features.auth.repositories import ExternalIdentityRepository

    next_url = session.pop("github_next_url", None)
    if not authentication_service.is_safe_redirect_target(next_url):
        next_url = None

    connect_mode = session.pop("github_connect_mode", False)

    try:
        token = current_app.github_service.github_client.authorize_access_token()
    except Exception as exc:
        current_app.logger.exception("GitHub authorize_access_token failed: %s", exc)
        flash("GitHub authorization failed (invalid session or provider error). Please try again.", "danger")
        return _back_to_login(next_url)

    user_info, err = current_app.github_service.get_github_user_info(token)
    if err:
        flash(err, "danger")
        return _back_to_login(next_url)

    if connect_mode:
        if not current_user.is_authenticated:
            flash("You must be logged in to connect GitHub.", "danger")
            return redirect(url_for("auth.login"))

        github_id = user_info.get("id")
        email = (user_info.get("email") or "").strip().lower() if user_info.get("email") else None
        external_repo = ExternalIdentityRepository()
        external_repo.create(user_id=current_user.id, provider="github", provider_id=github_id, email=email)
        flash("GitHub account connected successfully", "success")
        return redirect(url_for("profile.edit_profile"))
    else:
        user, err = current_app.github_service.get_or_create_user(user_info)
        if err:
            flash(err, "danger")
            return _back_to_login(next_url)

        login_user(user)
        flash("Signed in with GitHub.", "success")
        return redirect(next_url or url_for("public.index"))
