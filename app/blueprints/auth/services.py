from flask_login import login_user

from app.blueprints.auth.models import User


class AuthenticationService:

    @staticmethod
    def login(email, password, remember=True):
        user = User.get_by_email(email)
        if user is not None and user.check_password(password):
            login_user(user, remember=remember)
            return True
        return False
