from flask import request, render_template, flash
from flask_login import login_required

from app.blueprints.profile import profile_bp
from app.blueprints.profile.forms import UserProfileForm

from app import get_authenticated_user_profile


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
