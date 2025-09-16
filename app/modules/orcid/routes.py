from flask import current_app, redirect, url_for
from flask_login import login_user

from app.modules.orcid import orcid_bp
from app.modules.orcid.services import OrcidService


@orcid_bp.before_app_request
def before_request():
    current_app.orcid_service = OrcidService()


@orcid_bp.route("/orcid/login")
def login():
    redirect_uri = url_for("orcid.authorize", _external=True, _scheme="https")
    return current_app.orcid_service.orcid_client.authorize_redirect(redirect_uri)


@orcid_bp.route("/orcid/authorize")
def authorize():
    token = current_app.orcid_service.orcid_client.authorize_access_token()
    user_info = current_app.orcid_service.get_orcid_user_info(token)
    user = current_app.orcid_service.get_or_create_user(user_info)
    login_user(user)
    return redirect("/")
