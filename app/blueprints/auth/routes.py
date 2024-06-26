from flask import (render_template, redirect, url_for, request)
from flask_login import current_user, login_user, logout_user

from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import SignupForm, LoginForm
from app.blueprints.auth.services import AuthenticationService

from app.blueprints.profile.models import UserProfile


@auth_bp.route("/signup/", methods=["GET", "POST"])
def show_signup_form():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))
    form = SignupForm()
    error = None
    if form.validate_on_submit():
        name = form.name.data
        surname = form.surname.data
        email = form.email.data
        password = form.password.data

        from app.blueprints.auth.models import User
        user = User.get_by_email(email)
        if user is not None:
            error = f'Email {email} in use'
        else:
            # Create user
            user = User(email=email)
            user.set_password(password)
            user.save()

            # Create user profile
            profile = UserProfile(name=name, surname=surname)
            profile.user_id = user.id
            profile.save()

            # Log user
            login_user(user, remember=True)
            return redirect(url_for('public.index'))
    return render_template("auth/signup_form.html", form=form, error=error)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data
            if AuthenticationService.login(email, password):
                return redirect(url_for('public.index'))
            else:
                error = 'Invalid credentials'
                return render_template("auth/login_form.html", form=form, error=error)

    return render_template('auth/login_form.html', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('public.index'))
