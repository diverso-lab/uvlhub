import pytest

from app.features.auth.repositories import UserRepository
from app.features.orcid.repositories import OrcidRepository
from app.features.profile.repositories import UserProfileRepository

pytestmark = pytest.mark.repository


def test_get_by_orcid_id(test_app, clean_database):
    user = UserRepository().create(email="orcid@example.com", password="pw-123456")
    profile = UserProfileRepository().create(user_id=user.id, name="Ada", surname="Lovelace")
    repo = OrcidRepository()
    repo.create(orcid_id="0000-0001-2345-6789", profile_id=profile.id)

    assert repo.get_by_orcid_id("0000-0001-2345-6789") is not None
    assert repo.get_by_orcid_id("0000-0000-0000-0000") is None
