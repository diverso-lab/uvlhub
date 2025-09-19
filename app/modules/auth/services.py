import os

from flask_login import current_user, login_user

from app import db
from app.modules.auth.models import User
from app.modules.auth.repositories import UserRepository
from app.modules.profile.models import UserProfile
from app.modules.profile.repositories import UserProfileRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService


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

            # 🚨 Validación clave
            if not self.is_email_available(email):
                raise ValueError("This email is already registered. Try logging in or using ORCID.")

            user_data = {
                "email": email,
                "password": password,
                "active": False,
            }

            profile_data = {
                "name": name,
                "surname": surname,
            }

            user = self.create(commit=False, **user_data)
            profile_data["user_id"] = user.id
            self.user_profile_repository.create(**profile_data)
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

        # Solo actualizamos los campos que el usuario puede editar
        profile.name = form.name.data
        profile.surname = form.surname.data
        profile.affiliation = form.affiliation.data

        # 🚫 No tocar ORCID: se gestiona exclusivamente vía login OAuth
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
