import pytest

from app.features.apikeys.repositories import ApiKeyRepository
from app.features.auth.repositories import UserRepository

pytestmark = pytest.mark.repository


def _user(email="dev@example.com"):
    return UserRepository().create(email=email, password="pw-123456")


def test_create_then_get_by_key(test_app, clean_database):
    user = _user()
    ApiKeyRepository().create(key="abc123", user_id=user.id, scopes="read_dataset")

    found = ApiKeyRepository().get_by_key("abc123")

    assert found is not None
    assert found.user_id == user.id


def test_get_by_key_returns_none_when_absent(test_app, clean_database):
    assert ApiKeyRepository().get_by_key("missing") is None


def test_list_for_user_is_scoped_to_the_owner(test_app, clean_database):
    owner = _user()
    other = _user("other@example.com")
    repo = ApiKeyRepository()
    repo.create(key="k1", user_id=owner.id, scopes="read_dataset")
    repo.create(key="k2", user_id=owner.id, scopes="read_dataset")
    repo.create(key="k3", user_id=other.id, scopes="read_dataset")

    keys = repo.list_for_user(owner.id)

    assert {key.key for key in keys} == {"k1", "k2"}


def test_get_for_user_enforces_ownership(test_app, clean_database):
    owner = _user()
    other = _user("other@example.com")
    repo = ApiKeyRepository()
    api_key = repo.create(key="k1", user_id=owner.id, scopes="read_dataset")

    assert repo.get_for_user(api_key.id, owner.id) is not None
    assert repo.get_for_user(api_key.id, other.id) is None
