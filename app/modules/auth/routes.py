from flask import flash, render_template, redirect, url_for, request
from flask_login import current_user, login_user, logout_user

from app.modules.auth import auth_bp
from app.modules.auth.decorators import guest_required
from app.modules.auth.forms import SignupForm, LoginForm
from app.modules.auth.services import AuthenticationService
from app.modules.profile.services import UserProfileService
from app.modules.recaptcha.services import RecaptchaService
from core.configuration.configuration import is_production

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()
recaptcha_service = RecaptchaService()

@auth_bp.route("/signup/", methods=["GET", "POST"])
def show_signup_form():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    form = SignupForm()
    if form.validate_on_submit():

        if(is_production()):
            recaptcha_response = request.form.get('g-recaptcha-response')
            if not recaptcha_service.validate_recaptcha(recaptcha_response):
                flash('Please complete the reCAPTCHA', 'danger')
                return render_template('auth/signup_form.html', form=form)

        email = form.email.data
        if not authentication_service.is_email_available(email):
            return render_template("auth/signup_form.html", form=form, error=f'Email {email} in use')

        try:
            user = authentication_service.create_with_profile(**form.data)
        except Exception as exc:
            return render_template("auth/signup_form.html", form=form, error=f'Error creating user: {exc}')

        # Log user
        login_user(user, remember=True)
        return redirect(url_for('public.index'))

    return render_template("auth/signup_form.html", form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
@guest_required
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():

        if(is_production()):
            recaptcha_response = request.form.get('g-recaptcha-response')
            if not recaptcha_service.validate_recaptcha(recaptcha_response):
                flash('Please complete the reCAPTCHA', 'danger')
                return render_template('auth/login_form.html', form=form)

        if authentication_service.login(form.email.data, form.password.data):
            return redirect(url_for('public.index'))

        return render_template("auth/login_form.html", form=form, error='Invalid credentials')

    return render_template('auth/login_form.html', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('public.index'))
