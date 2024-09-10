from flask import flash, render_template, redirect, url_for, request
from flask_login import current_user, login_user, logout_user

from app.modules.auth import auth_bp
from app.modules.auth.decorators import guest_required
from app.modules.auth.forms import SignupForm, LoginForm
from app.modules.auth.services import AuthenticationService
from app.modules.profile.services import UserProfileService
from app.modules.captcha.services import CaptchaService

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()
captcha_service = CaptchaService()


@auth_bp.route("/signup/", methods=["GET", "POST"])
def show_signup_form():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    form = SignupForm()
    if form.validate_on_submit():

        user_input = request.form['captcha']
        if not captcha_service.validate_captcha(user_input):
            flash('Please complete the reCAPTCHA', 'danger')
            return render_template('auth/signup_form.html', form=form)

        email = form.email.data
        if not authentication_service.is_email_available(email):
            return render_template("auth/signup_form.html", form=form, error=f'Email {email} in use')

        try:
            user = authentication_service.create_with_profile(**form.data)
            authentication_service.send_confirmation_email(user.email)
            flash("Please confirm your email", "info")
        except Exception as exc:
            return render_template("auth/signup_form.html", form=form, error=f'Error creating user: {exc}')

        return redirect(url_for("public.index"))

    return render_template("auth/signup_form.html", form=form)


@auth_bp.route("/confirm_user/<token>", methods=["GET"])
def confirm_user(token):
    try:
        user = authentication_service.confirm_user_with_token(token)
    except Exception as exc:
        flash(exc.args[0], "danger")
        return redirect(url_for("auth.show_signup_form"))

    # Log user
    login_user(user, remember=True)
    return redirect(url_for("public.index"))


@auth_bp.route('/login', methods=['GET', 'POST'])
@guest_required
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():

        if authentication_service.login(form.email.data, form.password.data):
            return redirect(url_for('public.index'))

        return render_template("auth/login_form.html", form=form, error='Invalid credentials')

    return render_template('auth/login_form.html', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('public.index'))
