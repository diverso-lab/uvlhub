from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.features.auth.services import AuthenticationService
from app.features.profile import profile_bp
from app.features.profile.forms import UserProfileForm
from app.features.profile.services import UserProfileService

auth_service = AuthenticationService()
user_profile_service = UserProfileService()


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    profile = auth_service.get_authenticated_user_profile()
    if not profile:
        return redirect(url_for("public.index"))

    form = UserProfileForm(obj=profile)

    if form.validate_on_submit():
        result, errors = user_profile_service.update_profile(profile.id, form)
        if result:
            flash("Profile updated successfully", "success")
            return redirect(url_for("profile.edit_profile"))
        for error_field, error_messages in errors.items():
            for error_message in error_messages:
                flash(f"{error_field}: {error_message}", "error")
        return render_template("profile/edit.html", form=form)

    return render_template("profile/edit.html", form=form, profile=profile)


@profile_bp.route("/profile/summary")
@login_required
def my_profile():
    page = request.args.get("page", 1, type=int)
    pagination = user_profile_service.paginate_user_datasets(current_user.id, page=page)

    return render_template(
        "profile/summary.html",
        user_profile=current_user.profile,
        user=current_user,
        datasets=pagination.items,
        pagination=pagination,
        total_datasets=pagination.total,
    )


@profile_bp.route("/api/me", methods=["GET"])
@login_required
def get_my_profile():
    profile = current_user.profile
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    return jsonify(
        {
            "name": profile.name,
            "surname": profile.surname,
            "affiliation": profile.affiliation,
            "orcid": profile.get_orcid(),
        }
    )
