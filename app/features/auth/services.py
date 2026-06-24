import os
from urllib.parse import urljoin, urlparse

from flask import request, url_for
from flask_login import current_user, login_user
from splent_framework.configuration.configuration import uploads_folder_name
from splent_framework.services.BaseService import BaseService

from app.features.auth.models import User
from app.features.auth.repositories import UserRepository
from app.features.profile.models import UserProfile
from app.features.profile.repositories import UserProfileRepository
from app.managers.task_queue_manager import TaskQueueManager

CONFIRMATION_EMAIL_TASK = "app.features.auth.tasks.send_confirmation_email"


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
        email = (kwargs.get("email") or "").strip().lower()
        password = kwargs.get("password")
        name = kwargs.get("name")
        surname = kwargs.get("surname")

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

        try:
            # The repositories own persistence; the service only orchestrates the
            # user + profile pair as a single atomic unit of work.
            user = self.repository.create(commit=False, email=email, password=password, active=True)
            self.user_profile_repository.create(commit=False, user_id=user.id, name=name, surname=surname)
            self.repository.session.commit()
            return user
        except Exception:
            self.repository.session.rollback()
            raise

    def enqueue_confirmation_email(self, email: str) -> None:
        """Schedule the confirmation email for asynchronous delivery."""
        TaskQueueManager().enqueue_task(CONFIRMATION_EMAIL_TASK, email=email, timeout=10)

    def update_profile(self, user_profile_id, form):
        if not form.validate():
            return None, form.errors

        if self.user_profile_repository.get_by_id(user_profile_id) is None:
            return None, {"error": "Profile not found"}

        # Only update the fields the user is allowed to edit. ORCID is left
        # untouched on purpose: it is managed exclusively through the OAuth flow.
        profile = self.user_profile_repository.update(
            user_profile_id,
            name=form.name.data,
            surname=form.surname.data,
            affiliation=form.affiliation.data,
        )
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

    def activate_user(self, email: str) -> User:
        user = self.repository.get_by_email(email, active=None)
        if user is None:
            raise ValueError(f"No account is associated with {email}.")
        if not user.active:
            self.repository.update(user.id, active=True)
        return user

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
