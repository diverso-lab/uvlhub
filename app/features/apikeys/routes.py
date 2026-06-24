from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.features.apikeys import apikeys_bp
from app.features.apikeys.services import ApiKeyService

api_key_service = ApiKeyService()


@apikeys_bp.route("/apikeys", methods=["GET"])
def index():
    return render_template("apikeys/index.html")


@apikeys_bp.route("/developer/api-keys/generate", methods=["GET", "POST"])
@login_required
def generate_api_key():
    if request.method == "POST":
        scopes = request.form.getlist("scopes")
        api_key, token = api_key_service.generate_for_user(current_user, scopes)
        return render_template("developer/show_key.html", api_key=api_key, token=token, scopes=scopes)

    return render_template("developer/generate_key.html")


@apikeys_bp.route("/developer/api-keys", methods=["GET"])
@login_required
def list_api_keys():
    keys = api_key_service.list_for_user(current_user)
    return render_template("developer/list_keys.html", api_keys=keys)


@apikeys_bp.route("/developer/api-keys/delete", methods=["POST"])
@login_required
def delete_api_key():
    key_id = request.form.get("key_id")
    if api_key_service.delete_for_user(key_id, current_user):
        flash("API key deleted successfully", "success")
    else:
        flash("API key not found or not yours", "danger")
    return redirect(url_for("apikeys.list_api_keys"))
