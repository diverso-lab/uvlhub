"""Repository-level tests for the github feature.

These test data access without the HTTP layer or services.
"""

import pytest

from app import db
from app.features.auth.models import User
from app.features.github.models import Github
from app.features.github.repositories import GithubRepository
from app.features.profile.models import UserProfile

pytestmark = pytest.mark.repository


def test_get_by_github_id_returns_record_when_exists(test_app, clean_database):
    user = User.query.first() or User(password="test", active=True)
    if not user.id:
        db.session.add(user)
        db.session.flush()

    profile = UserProfile(user_id=user.id, name="Test", surname="User")
    github = Github(github_id=12345, github_login="testuser", profile_id=None)

    db.session.add(profile)
    db.session.flush()
    github.profile_id = profile.id
    db.session.add(github)
    db.session.commit()

    repo = GithubRepository()
    result = repo.get_by_github_id(12345)

    assert result is not None
    assert result.github_login == "testuser"


def test_get_by_github_id_returns_none_when_not_exists(test_app, clean_database):
    repo = GithubRepository()
    result = repo.get_by_github_id(99999)

    assert result is None
