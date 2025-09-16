from flask import flash, redirect, render_template, request, url_for

from app.modules.auth.decorators import guest_required
from app.modules.reset import reset_bp
from app.modules.reset.services import ResetService

reset_service = ResetService()


@reset_bp.route("/reset/forgot", methods=["GET", "POST"])
@guest_required
def forgot():
    if request.method == "POST":

        email = request.form["email"]
        token = reset_service.send_reset_password_mail(email=email)
        reset_service.add_token(token=token)

        try:
            email = request.form["email"]
            token = reset_service.send_reset_password_mail(email=email)
            reset_service.add_token(token=token)
            flash(
                "Check your email for the instructions to reset your password",
                "success",
            )
        except Exception as exc:
            flash(f"An error occurred while trying to reset the password: {exc}", "danger")

        return redirect(url_for("auth.login"))
    return render_template("forgot/forgot.html")


@reset_bp.route("/reset/password/<token>", methods=["GET", "POST"])
@guest_required
def reset_password(token):

    reset_service.check_valid_token(token)
    email = reset_service.get_email_by_token(token)

    if reset_service.token_already_used(token):
        flash("This reset link has already been used.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        password = request.form["password"]
        reset_service.reset_password(email=email, password=password)
        reset_service.mark_token_as_used(token)
        flash("Your password has been updated!", "success")
        return redirect(url_for("auth.login"))
    return render_template("forgot/reset_password.html")
