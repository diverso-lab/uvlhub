from flask import request, render_template
from flask_login import login_required, current_user

from app.blueprints.profile import profile_bp
from app.blueprints.profile.forms import UserProfileForm
from app.blueprints.dataset.models import DataSet

from app import get_authenticated_user_profile, db
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


@profile_bp.route('/profile/summary')
@login_required
def my_profile():
    page = request.args.get('page', 1, type=int)
    per_page = 5

    user_datasets_pagination = db.session.query(DataSet) \
        .filter(DataSet.user_id == current_user.id) \
        .order_by(DataSet.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    total_datasets_count = db.session.query(DataSet) \
        .filter(DataSet.user_id == current_user.id) \
        .count()

    print(user_datasets_pagination.items)

    return render_template(
        'profile/summary.html',
        user_profile=current_user.profile,
        user=current_user,
        datasets=user_datasets_pagination.items,
        pagination=user_datasets_pagination,
        total_datasets=total_datasets_count
    )
