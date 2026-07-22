from flask import flash, jsonify, redirect, render_template, request, session, url_for
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
    from app.features.auth.repositories import ExternalIdentityRepository

    profile = auth_service.get_authenticated_user_profile()
    if not profile:
        return redirect(url_for("public.index"))

    form = UserProfileForm(obj=profile)
    external_repo = ExternalIdentityRepository()
    identities = external_repo.get_all_by_user(current_user.id)

    if form.validate_on_submit():
        result, errors = user_profile_service.update_profile(profile.id, form)
        if result:
            flash("Profile updated successfully", "success")
            return redirect(url_for("profile.edit_profile"))
        for error_field, error_messages in errors.items():
            for error_message in error_messages:
                flash(f"{error_field}: {error_message}", "error")
        return render_template("profile/edit.html", form=form, identities=identities)

    return render_template("profile/edit.html", form=form, profile=profile, identities=identities)


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


@profile_bp.route("/account/connect/github")
@login_required
def connect_github():
    from flask import session as flask_session

    flask_session["github_connect_mode"] = True
    return redirect(url_for("github.login"))


@profile_bp.route("/account/connect/orcid")
@login_required
def connect_orcid():
    session["orcid_connect_mode"] = True
    return redirect(url_for("orcid.login"))


@profile_bp.route("/account/connect/orcid-with-email", methods=["POST"])
@login_required
def connect_orcid_with_email():
    email = request.form.get("email", "").strip().lower()
    if not email:
        flash("Email is required.", "danger")
        return redirect(url_for("profile.edit_profile"))

    session["orcid_connect_mode"] = True
    session["orcid_connect_email"] = email
    return redirect(url_for("orcid.login"))
