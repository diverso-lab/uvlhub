import pytest

from app.features.auth.repositories import UserRepository
from app.features.profile.repositories import UserProfileRepository

pytestmark = pytest.mark.repository


def _user(email="profile@example.com"):
    return UserRepository().create(email=email, password="pw-123456")


def test_create_then_fetch_profile(test_app, clean_database):
    user = _user()
    repo = UserProfileRepository()

    profile = repo.create(user_id=user.id, name="Ada", surname="Lovelace")

    assert repo.get_by_id(profile.id).name == "Ada"


def test_update_changes_persisted_fields(test_app, clean_database):
    user = _user()
    repo = UserProfileRepository()
    profile = repo.create(user_id=user.id, name="Ada", surname="Lovelace")

    repo.update(profile.id, affiliation="Analytical Engine Co.")

    assert repo.get_by_id(profile.id).affiliation == "Analytical Engine Co."
