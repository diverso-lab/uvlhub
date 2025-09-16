from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.modules.apikeys import apikeys_bp
from app.modules.apikeys.models import ApiKey


@apikeys_bp.route("/apikeys", methods=["GET"])
def index():
    return render_template("apikeys/index.html")


@apikeys_bp.route("/developer/api-keys/generate", methods=["GET", "POST"])
@login_required
def generate_api_key():
    if request.method == "POST":
        scopes = request.form.getlist("scopes")  # ['read_dataset']
        api_key_obj, token = ApiKey.generate(user=current_user, scopes=scopes)
        return render_template("developer/show_key.html", api_key=api_key_obj, token=token, scopes=scopes)

    return render_template("developer/generate_key.html")


@apikeys_bp.route("/developer/api-keys", methods=["GET"])
@login_required
def list_api_keys():
    keys = ApiKey.query.filter_by(user_id=current_user.id).order_by(ApiKey.created_at.desc()).all()
    return render_template("developer/list_keys.html", api_keys=keys)


@apikeys_bp.route("/developer/api-keys/delete", methods=["POST"])
@login_required
def delete_api_key():
    key_id = request.form.get("key_id")
    api_key = ApiKey.query.filter_by(id=key_id, user_id=current_user.id).first()
    if not api_key:
        flash("API key not found or not yours", "danger")
        return redirect(url_for("apikeys.list_api_keys"))

    db.session.delete(api_key)
    db.session.commit()
    flash("API key deleted successfully", "success")
    return redirect(url_for("apikeys.list_api_keys"))
