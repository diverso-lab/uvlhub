from flask import request, render_template, flash, redirect, url_for, Blueprint
from flask_login import login_required, current_user

from app.profile import profile_bp
from app.profile.forms import UserProfileForm

from .models import UserProfile
from .. import get_authenticated_user_profile


@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = UserProfileForm()

    if request.method == 'POST' and form.validate_on_submit():
        orcid = form.orcid.data.strip()
        name = form.name.data.strip()
        surname = form.surname.data.strip()
        affiliation = form.affiliation.data.strip()

        profile = get_authenticated_user_profile()
        profile.orcid = orcid
        profile.name = name
        profile.surname = surname
        profile.affiliation = affiliation
        profile.save()

        flash('Saved profile', 'success')

        return render_template('profile/edit.html', form=form)

    else:
        return render_template('profile/edit.html', form=form)


@profile_bp.route('/myProfile')
@login_required
def my_profile():
    user_datasets = current_user.data_sets
    return render_template('profile/myProfile.html', user_profile=current_user.profile, user=current_user, datasets=user_datasets)

