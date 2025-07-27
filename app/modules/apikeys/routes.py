from flask import render_template, request
from flask_login import current_user, login_required
from app.modules.apikeys import apikeys_bp
from app.modules.apikeys.models import ApiKey


@apikeys_bp.route('/apikeys', methods=['GET'])
def index():
    return render_template('apikeys/index.html')


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
    keys = current_user.api_keys
    return render_template("developer/list_keys.html", api_keys=keys)
