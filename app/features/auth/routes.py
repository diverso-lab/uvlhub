from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app.features.auth import auth_bp
from app.features.auth.decorators import guest_required
from app.features.auth.forms import LoginForm, SignupForm
from app.features.auth.services import AuthenticationService
from app.features.captcha.services import CaptchaService

authentication_service = AuthenticationService()
captcha_service = CaptchaService()


@auth_bp.route("/signup/", methods=["GET", "POST"])
def signup():
    next_url = authentication_service.get_safe_next_url()
    if current_user.is_authenticated:
        return redirect(next_url or url_for("public.index"))

    form = SignupForm()

    if request.method == "POST" and form.validate_on_submit():
        if not authentication_service.is_email_available(form.email.data):
            flash(f"The email '{form.email.data}' is already registered.", "danger")
            return render_template("auth/signup_form.html", form=form, next_url=next_url)

        if not captcha_service.validate_captcha(request.form.get("captcha", "")):
            flash("Please complete the CAPTCHA correctly.", "danger")
            return render_template("auth/signup_form.html", form=form, next_url=next_url)

        try:
            user = authentication_service.create_with_profile(**form.data)
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("auth/signup_form.html", form=form, next_url=next_url)

        login_user(user, remember=True)
        flash("Account created successfully. Welcome!", "success")
        authentication_service.enqueue_confirmation_email(user.email)
        return redirect(next_url or url_for("public.index"))

    return render_template("auth/signup_form.html", form=form, next_url=next_url)


@auth_bp.route("/login", methods=["GET", "POST"])
@guest_required
def login():
    next_url = authentication_service.get_safe_next_url()
    if current_user.is_authenticated:
        return redirect(next_url or url_for("public.index"))

    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():

        if authentication_service.login(form.email.data, form.password.data):
            return redirect(next_url or url_for("public.index"))

        return render_template("auth/login_form.html", form=form, error="Invalid credentials", next_url=next_url)

    return render_template("auth/login_form.html", form=form, next_url=next_url)


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("public.index"))


@auth_bp.route("/api/v1/auth/status", methods=["GET"])
def auth_status():
    payload, status_code = authentication_service.get_flamapy_ide_auth_status_payload()
    return jsonify(payload), status_code
