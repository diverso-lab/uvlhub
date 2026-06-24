import pytest

from app.features.auth.models import User

pytestmark = pytest.mark.unit


def test_set_password_does_not_store_plaintext():
    user = User(email="user@example.com", password="s3cr3t-password")

    assert user.password != "s3cr3t-password"


def test_check_password_accepts_the_original_value():
    user = User(email="user@example.com", password="s3cr3t-password")

    assert user.check_password("s3cr3t-password") is True


def test_check_password_rejects_a_wrong_value():
    user = User(email="user@example.com", password="s3cr3t-password")

    assert user.check_password("wrong-password") is False


def test_repr_contains_the_email():
    user = User(email="user@example.com", password="s3cr3t-password")

    assert "user@example.com" in repr(user)
