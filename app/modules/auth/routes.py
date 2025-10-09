from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from pymysql import IntegrityError

from app import db
from app.modules.auth import auth_bp
from app.modules.auth.decorators import guest_required
from app.modules.auth.forms import LoginForm, SignupForm
from app.modules.auth.services import AuthenticationService
from app.modules.captcha.services import CaptchaService
from app.modules.confirmemail.services import ConfirmemailService
from app.modules.profile.services import UserProfileService
from core.managers.task_queue_manager import TaskQueueManager

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()
captcha_service = CaptchaService()
confirmemail_service = ConfirmemailService()


@auth_bp.route("/signup/", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = SignupForm()

    if request.method == "POST" and form.validate_on_submit():
        email = form.email.data.strip().lower()

        if not authentication_service.is_email_available(email):
            flash(f"The email '{email}' is already registered.", "danger")
            return render_template("auth/signup_form.html", form=form)

        user_input = request.form.get("captcha", "")
        if not captcha_service.validate_captcha(user_input):
            flash("Please complete the CAPTCHA correctly.", "danger")
            return render_template("auth/signup_form.html", form=form)

        try:
            user = authentication_service.create_with_profile(**form.data)
            login_user(user, remember=True)
            flash("Account created successfully. Welcome!", "success")

            print(">>> SIGNUP reached end: before enqueuing email", flush=True)

            task_manager = TaskQueueManager()
            task_manager.enqueue_task("app.modules.auth.tasks.send_confirmation_email", email=user.email, timeout=10)

            return redirect(url_for("public.index"))

        except IntegrityError:
            db.session.rollback()
            flash("An error occurred while creating your account.", "danger")

    return render_template("auth/signup_form.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@guest_required
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():

        if authentication_service.login(form.email.data, form.password.data):
            return redirect(url_for("public.index"))

        return render_template("auth/login_form.html", form=form, error="Invalid credentials")

    return render_template("auth/login_form.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("public.index"))
