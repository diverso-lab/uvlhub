import pytest

from app.features.auth.repositories import UserRepository

pytestmark = pytest.mark.repository


def test_create_hashes_the_password_and_persists(test_app, clean_database):
    repo = UserRepository()

    user = repo.create(email="repo@example.com", password="pw-123456")

    assert user.id is not None
    assert user.password != "pw-123456"
    assert user.check_password("pw-123456") is True
    assert repo.count() == 1


def test_get_by_email_normalises_case_and_whitespace(test_app, clean_database):
    repo = UserRepository()
    repo.create(email="Mixed@Example.com", password="pw-123456")

    assert repo.get_by_email("  mixed@example.com  ") is not None


def test_get_by_email_returns_none_when_absent(test_app, clean_database):
    assert UserRepository().get_by_email("absent@example.com") is None


def test_get_by_email_honours_the_active_filter(test_app, clean_database):
    repo = UserRepository()
    repo.create(email="inactive@example.com", password="pw-123456", active=False)

    assert repo.get_by_email("inactive@example.com", active=True) is None
    assert repo.get_by_email("inactive@example.com", active=False) is not None
