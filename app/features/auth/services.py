import os
from urllib.parse import urljoin, urlparse

from flask import request, url_for
from flask_login import current_user, login_user

from app import db
from app.features.auth.models import User
from app.features.auth.repositories import UserRepository
from app.features.profile.models import UserProfile
from app.features.profile.repositories import UserProfileRepository
from splent_framework.configuration.configuration import uploads_folder_name
from splent_framework.services.BaseService import BaseService


class AuthenticationService(BaseService):

    def __init__(self):
        super().__init__(UserRepository())
        self.user_profile_repository = UserProfileRepository()

    def login(self, email, password, remember=True):
        user = self.repository.get_by_email(email)
        if user is not None and user.check_password(password):
            login_user(user, remember=remember)
            return True
        return False

    def is_email_available(self, email: str) -> bool:
        return self.repository.get_by_email(email) is None

    def create_with_profile(self, **kwargs):
        try:
            email = kwargs.pop("email", None)
            password = kwargs.pop("password", None)
            name = kwargs.pop("name", None)
            surname = kwargs.pop("surname", None)

            if not email:
                raise ValueError("Email is required.")
            if not password:
                raise ValueError("Password is required.")
            if not name:
                raise ValueError("Name is required.")
            if not surname:
                raise ValueError("Surname is required.")

            if not self.is_email_available(email):
                raise ValueError("This email is already registered. Try logging in or using ORCID.")

            # Create user
            user = User(email=email, active=True)
            user.set_password(password)
            self.repository.session.add(user)
            self.repository.session.flush()  # guarantees user.id is available

            # Create profile
            profile = UserProfile(user_id=user.id, name=name, surname=surname)
            self.repository.session.add(profile)
            self.repository.session.commit()

            return user

        except Exception as exc:
            self.repository.session.rollback()
            raise exc

    def update_profile(self, user_profile_id, form):
        if not form.validate():
            return None, form.errors

        profile = UserProfile.query.get(user_profile_id)
        if not profile:
            return None, {"error": "Profile not found"}

        # Only update fields the user is allowed to edit
        profile.name = form.name.data
        profile.surname = form.surname.data
        profile.affiliation = form.affiliation.data

        # Do NOT touch ORCID: it is managed exclusively through the OAuth login flow.
        db.session.commit()
        return profile, None

    def get_authenticated_user(self) -> User | None:
        if current_user.is_authenticated:
            return current_user
        return None

    def get_authenticated_user_profile(self) -> UserProfile | None:
        if current_user.is_authenticated:
            return current_user.profile
        return None

    def temp_folder_by_user(self, user: User) -> str:
        return os.path.join(uploads_folder_name(), "temp", str(user.id))

    def get_by_email(self, email: str, active: bool = True) -> User:
        return self.repository.get_by_email(email, active)

    def is_safe_redirect_target(self, target: str | None) -> bool:
        if not target:
            return False

        ref_url = urlparse(request.host_url)
        test_url = urlparse(urljoin(request.host_url, target))
        return test_url.scheme in {"http", "https"} and test_url.netloc == ref_url.netloc

    def get_safe_next_url(self) -> str | None:
        next_url = request.form.get("next") or request.args.get("next")
        if self.is_safe_redirect_target(next_url):
            return next_url
        return None

    def get_flamapy_ide_auth_links(self) -> dict:
        return {
            "login_url": url_for("auth.login", _external=True),
            "signup_url": url_for("auth.signup", _external=True),
            "orcid_url": url_for("orcid.login", _external=True),
        }

    def get_flamapy_ide_auth_status_payload(self) -> tuple[dict, int]:
        user = self.get_authenticated_user()
        if not user:
            payload = {
                "authenticated": False,
                "message": "You need to sign in before saving a model from flamapyIDE to UVLHub.",
                **self.get_flamapy_ide_auth_links(),
            }
            return payload, 401

        profile = self.get_authenticated_user_profile()
        payload = {
            "authenticated": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": profile.name if profile else None,
                "surname": profile.surname if profile else None,
                "affiliation": profile.affiliation if profile else None,
                "orcid": profile.get_orcid() if profile else None,
            },
        }
        return payload, 200
