from flask import (render_template, redirect, url_for,
                   request, current_app)
from flask_login import current_user, login_user, logout_user

from app.auth import auth_bp
from app.auth.forms import SignupForm, LoginForm

from app.profile.models import UserProfile


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

        from app.auth.models import User
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
    if form.validate_on_submit():
        from app.auth.models import User
        user = User.get_by_email(form.email.data)

        if user is not None and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('public.index'))
        else:
            error = f'Invalid credentials'
            return render_template("auth/login_form.html", form=form, error=error)

    return render_template('auth/login_form.html', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('public.index'))
