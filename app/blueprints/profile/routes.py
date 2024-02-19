from flask import request, render_template, flash, redirect, url_for, current_app
from flask_login import login_required

from app.blueprints.profile import profile_bp
from app.blueprints.profile.forms import UserProfileForm

from app import get_authenticated_user_profile
from app.blueprints.profile.services import UserProfileService


@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = UserProfileForm()
    if request.method == 'POST':

        service = UserProfileService()
        result, errors = service.update_profile(get_authenticated_user_profile().id, form)
        return service.handle_service_response(result, errors, 'profile.edit_profile', 'Profile updated successfully',
                                               'profile/edit.html', form)

    return render_template('profile/edit.html', form=form)
