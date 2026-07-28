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


def test_generate_for_user_drops_unknown_scopes(test_app, clean_database):
    user = _user()

    api_key, _ = ApiKeyService().generate_for_user(user, ["read_dataset", "admin", "delete_everything"])

    assert api_key.scope_list == ["read_dataset"]


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


def test_get_valid_key_refuses_a_key_whose_owner_is_deactivated(test_app, clean_database):
    # Deactivating an account used to leave its keys fully usable, and
    # write_dataset publishes permanent public records to Zenodo. The transfer
    # endpoints already refuse an inactive recipient; the caller is checked for
    # the same reason.
    from app import db

    user = _user()
    service = ApiKeyService()
    _, token = service.generate_for_user(user, ["read_dataset", "write_dataset"])
    assert service.get_valid_key(token) is not None

    user.active = False
    db.session.commit()

    assert service.get_valid_key(token) is None


def test_get_valid_key_accepts_a_key_whose_owner_is_reactivated(test_app, clean_database):
    from app import db

    user = _user()
    service = ApiKeyService()
    _, token = service.generate_for_user(user, ["read_dataset"])

    user.active = False
    db.session.commit()
    assert service.get_valid_key(token) is None

    user.active = True
    db.session.commit()

    assert service.get_valid_key(token) is not None
