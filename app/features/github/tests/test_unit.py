import pytest

from app.features.auth.models import User
from app.features.github.models import Github
from app.features.profile.models import UserProfile

pytestmark = pytest.mark.unit


def test_github_model_repr(test_app, clean_database):
    github = Github(github_id=12345, github_login="octocat")
    assert repr(github) == "Github<octocat>"


def test_user_profile_get_github_returns_login_when_exists(test_app, clean_database):
    from app import db

    user = User(password="test", active=True)
    db.session.add(user)
    db.session.flush()

    profile = UserProfile(user_id=user.id, name="Test", surname="User")
    db.session.add(profile)
    db.session.flush()

    github = Github(github_id=12345, github_login="octocat", profile_id=profile.id)
    db.session.add(github)
    db.session.commit()

    # Refresh profile para cargar relación
    db.session.refresh(profile)

    assert profile.get_github() == "octocat"


def test_user_profile_get_github_returns_none_when_not_exists(test_app, clean_database):
    from app import db

    user = User(password="test", active=True)
    db.session.add(user)
    db.session.flush()

    profile = UserProfile(user_id=user.id, name="Test", surname="User")
    db.session.add(profile)
    db.session.commit()

    assert profile.get_github() is None
