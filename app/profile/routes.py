from flask import request, render_template, flash, redirect, url_for, Blueprint
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app import db

from app.profile import profile_bp
from app.profile.forms import UserProfileForm
from app.dataset.models import DataSet

from .models import UserProfile
from .. import get_authenticated_user_profile
from .services import valid_edit_form  


@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = UserProfileForm()

    if request.method == 'POST' and form.validate_on_submit():
        return valid_edit_form(form)

    else:
        return render_template('profile/edit.html', form=form)


@profile_bp.route('/myProfile')
@login_required
def my_profile():
    page = request.args.get('page', 1, type=int)
    per_page = 5
  
    user_datasets_pagination = db.session.query(DataSet) \
        .filter(DataSet.user_id == current_user.id) \
        .paginate(page=page, per_page=per_page, error_out=False)
    
    total_datasets_count = db.session.query(DataSet) \
        .filter(DataSet.user_id == current_user.id) \
        .count()

    print(user_datasets_pagination.items)
  
    return render_template(
        'profile/myProfile.html', 
        user_profile=current_user.profile, 
        user=current_user, 
        datasets=user_datasets_pagination.items, 
        pagination=user_datasets_pagination,
        total_datasets=total_datasets_count  
    )


