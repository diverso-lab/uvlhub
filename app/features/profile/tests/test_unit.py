import pytest

from app.features.profile.models import UserProfile

pytestmark = pytest.mark.unit


def test_get_orcid_returns_none_without_a_linked_orcid():
    assert UserProfile(name="Ada", surname="Lovelace").get_orcid() is None
