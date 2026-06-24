from types import SimpleNamespace

import pytest

from app.features.auth.repositories import UserRepository
from app.features.profile.repositories import UserProfileRepository
from app.features.profile.services import UserProfileService

pytestmark = pytest.mark.service


def _form(valid=True, **data):
    fields = {key: SimpleNamespace(data=value) for key, value in data.items()}
    return SimpleNamespace(validate=lambda: valid, errors={"name": ["This field is required."]}, **fields)


def test_update_profile_writes_only_the_allowed_fields(test_app, clean_database):
    user = UserRepository().create(email="profile@example.com", password="pw-123456")
    profile = UserProfileRepository().create(user_id=user.id, name="Ada", surname="Lovelace")

    result, errors = UserProfileService().update_profile(
        profile.id, _form(name="Grace", surname="Hopper", affiliation="Navy")
    )

    assert errors is None
    assert result.name == "Grace"
    assert result.surname == "Hopper"
    assert result.affiliation == "Navy"


def test_update_profile_returns_errors_when_invalid(test_app, clean_database):
    result, errors = UserProfileService().update_profile(1, _form(valid=False))

    assert result is None
    assert errors == {"name": ["This field is required."]}
