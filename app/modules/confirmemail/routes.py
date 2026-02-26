from flask import flash, redirect, render_template, url_for
from flask_login import login_user

from app.modules.confirmemail import confirmemail_bp
from app.modules.confirmemail.services import ConfirmemailService

confirmemail_service = ConfirmemailService()


@confirmemail_bp.route("/confirmemail", methods=["GET"])
def index():
    return render_template("confirmemail/index.html")


@confirmemail_bp.route("/confirm_user/<token>", methods=["GET"])
def confirm_user(token):
    try:
        user = confirmemail_service.confirm_user_with_token(token)
    except Exception as exc:
        flash(exc.args[0], "danger")
        return redirect(url_for("auth.signup"))

    # Log user
    login_user(user, remember=True)
    return redirect(url_for("public.index"))
