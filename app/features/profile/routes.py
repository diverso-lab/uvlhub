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
    from app.features.github.services import GithubService

    service = GithubService()
    redirect_uri = url_for("profile.connect_github_callback", _external=True)
    return service.github_client.authorize_redirect(redirect_uri)


@profile_bp.route("/account/connect/github/callback")
@login_required
def connect_github_callback():
    from app.features.github.services import GithubService
    from app.features.auth.repositories import ExternalIdentityRepository

    service = GithubService()
    token = service.github_client.authorize_access_token()
    user_info, err = service.get_github_user_info(token)

    if err:
        flash(err, "danger")
        return redirect(url_for("profile.edit_profile"))

    github_id = user_info.get("id")
    email = (user_info.get("email") or "").strip().lower() if user_info.get("email") else None
    github_login = (user_info.get("login") or "").strip()

    external_repo = ExternalIdentityRepository()
    external_repo.create(user_id=current_user.id, provider="github", provider_id=github_id, email=email)

    flash("GitHub account connected successfully", "success")
    return redirect(url_for("profile.edit_profile"))


@profile_bp.route("/account/connect/orcid")
@login_required
def connect_orcid():
    from app.features.orcid.services import OrcidService

    service = OrcidService()
    redirect_uri = url_for("profile.connect_orcid_callback", _external=True)
    return service.orcid_client.authorize_redirect(redirect_uri)


@profile_bp.route("/account/connect/orcid/callback")
@login_required
def connect_orcid_callback():
    from app.features.orcid.services import OrcidService
    from app.features.auth.repositories import ExternalIdentityRepository

    service = OrcidService()
    token = service.orcid_client.authorize_access_token()
    user_info, err = service.get_orcid_user_info(token)

    if err:
        flash(err, "danger")
        return redirect(url_for("profile.edit_profile"))

    orcid_id = (user_info.get("sub") or "").strip()

    external_repo = ExternalIdentityRepository()
    external_repo.create(user_id=current_user.id, provider="orcid", provider_id=orcid_id, email=None)

    flash("ORCID account connected successfully", "success")
    return redirect(url_for("profile.edit_profile"))
