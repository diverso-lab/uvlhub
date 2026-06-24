from flask import flash, redirect, render_template, url_for
from flask_login import login_user

from app.features.confirmemail import confirmemail_bp
from app.features.confirmemail.services import ConfirmemailService, EmailConfirmationError

confirmemail_service = ConfirmemailService()


@confirmemail_bp.route("/confirmemail", methods=["GET"])
def index():
    return render_template("confirmemail/index.html")


@confirmemail_bp.route("/confirm_user/<token>", methods=["GET"])
def confirm_user(token):
    try:
        user = confirmemail_service.confirm_user_with_token(token)
    except (EmailConfirmationError, ValueError) as exc:
        flash(str(exc), "danger")
        return redirect(url_for("auth.signup"))

    login_user(user, remember=True)
    return redirect(url_for("public.index"))
