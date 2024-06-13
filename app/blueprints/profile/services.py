from .models import UserProfile
from flask import flash, render_template
from .. import get_authenticated_user_profile

def valid_edit_form(form):
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

    