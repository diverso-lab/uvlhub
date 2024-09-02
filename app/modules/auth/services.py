import os

from flask import current_app, url_for
from flask_login import login_user
from flask_login import current_user
from itsdangerous import BadTimeSignature, SignatureExpired, URLSafeTimedSerializer

from app import mail_service
from app.modules.auth.models import User
from app.modules.auth.repositories import UserRepository
from app.modules.profile.models import UserProfile
from app.modules.profile.repositories import UserProfileRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService


class AuthenticationService(BaseService):
    SALT = "user-confirm"
    MAX_AGE = 3600

    def __init__(self):
        super().__init__(UserRepository())
        self.user_profile_repository = UserProfileRepository()

    def get_serializer(self):
        return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

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
        except Exception as exc:
            self.repository.session.rollback()
            raise exc
        return user

    def get_token_from_email(self, email):
        s = self.get_serializer()
        return s.dumps(email, salt=self.SALT)

    def send_confirmation_email(self, user_email):
        token = self.get_token_from_email(user_email)
        url = url_for("auth.confirm_user", token=token)
        mail_service.send_email(
            "Please confirm your email",
            recipients=[user_email],
            body=f"<a href='{url}'>Please confirm your email</a>",
        )

    def confirm_user_with_token(self, token):
        s = self.get_serializer()
        try:
            email = s.loads(token, salt=self.SALT, max_age=self.MAX_AGE)
        except SignatureExpired:
            raise Exception("The confirmation link has expired.")
        except BadTimeSignature:
            raise Exception("The confirmation link has been tampered with.")

        user = self.repository.get_by_email(email, active=False)
        user.active = True
        self.repository.session.commit()
        return user

    def update_profile(self, user_profile_id, form):
        if form.validate():
            updated_instance = self.update(user_profile_id, **form.data)
            return updated_instance, None

        return None, form.errors

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
