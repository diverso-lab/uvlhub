import pytest

from app.features.apikeys.repositories import ApiKeyRepository
from app.features.apikeys.services import ApiKeyService
from app.features.auth.repositories import UserRepository

pytestmark = pytest.mark.service


def _user(email="dev@example.com"):
    return UserRepository().create(email=email, password="pw-123456")


def test_generate_for_user_persists_and_returns_a_token(test_app, clean_database):
    user = _user()

    api_key, token = ApiKeyService().generate_for_user(user, ["read_dataset", "write_dataset"])

    assert len(token) == 64
    assert api_key.key == token
    assert api_key.scope_list == ["read_dataset", "write_dataset"]
    assert ApiKeyRepository().count() == 1


def test_list_for_user_returns_only_the_owners_keys(test_app, clean_database):
    owner = _user()
    other = _user("other@example.com")
    service = ApiKeyService()
    service.generate_for_user(owner, ["read_dataset"])
    service.generate_for_user(other, ["read_dataset"])

    assert len(service.list_for_user(owner)) == 1


def test_delete_for_user_returns_true_then_false(test_app, clean_database):
    user = _user()
    service = ApiKeyService()
    api_key, _ = service.generate_for_user(user, ["read_dataset"])

    assert service.delete_for_user(api_key.id, user) is True
    assert service.delete_for_user(api_key.id, user) is False


def test_delete_for_user_rejects_another_users_key(test_app, clean_database):
    owner = _user()
    other = _user("other@example.com")
    service = ApiKeyService()
    api_key, _ = service.generate_for_user(owner, ["read_dataset"])

    assert service.delete_for_user(api_key.id, other) is False
    assert ApiKeyRepository().count() == 1


def test_get_valid_key_and_mark_used(test_app, clean_database):
    user = _user()
    service = ApiKeyService()
    _, token = service.generate_for_user(user, ["read_dataset"])

    api_key = service.get_valid_key(token)
    assert api_key is not None
    assert api_key.last_used_at is None

    service.mark_used(api_key)
    assert service.get_valid_key(token).last_used_at is not None
