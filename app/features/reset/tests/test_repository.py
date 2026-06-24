import pytest

from app.features.reset.repositories import ResetRepository

pytestmark = pytest.mark.repository


def test_get_by_token_returns_the_record(test_app, clean_database):
    repo = ResetRepository()
    repo.create(token="tok-123")

    assert repo.get_by_token("tok-123") is not None


def test_get_by_token_returns_none_when_absent(test_app, clean_database):
    assert ResetRepository().get_by_token("missing") is None
