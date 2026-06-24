from unittest.mock import patch

import pytest

from app.features.auth.repositories import UserRepository
from app.features.auth.services import CONFIRMATION_EMAIL_TASK, AuthenticationService
from app.features.profile.repositories import UserProfileRepository

pytestmark = pytest.mark.service


def test_is_email_available_for_an_unused_address(test_app, clean_database):
    assert AuthenticationService().is_email_available("free@example.com") is True


def test_is_email_available_is_false_once_taken(test_app, clean_database):
    UserRepository().create(email="taken@example.com", password="pw-123456")

    assert AuthenticationService().is_email_available("taken@example.com") is False


def test_create_with_profile_persists_user_and_profile(test_app, clean_database):
    user = AuthenticationService().create_with_profile(
        name="Ada", surname="Lovelace", email="ada@example.com", password="pw-123456"
    )

    assert user.active is True
    assert UserRepository().count() == 1
    assert UserProfileRepository().count() == 1


@pytest.mark.parametrize(
    "missing, message",
    [
        ("email", "Email is required."),
        ("password", "Password is required."),
        ("name", "Name is required."),
        ("surname", "Surname is required."),
    ],
)
def test_create_with_profile_validates_required_fields(test_app, clean_database, missing, message):
    data = {"name": "Ada", "surname": "Lovelace", "email": "ada@example.com", "password": "pw-123456"}
    data[missing] = ""

    with pytest.raises(ValueError, match=message):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


def test_create_with_profile_rejects_a_duplicate_email(test_app, clean_database):
    service = AuthenticationService()
    service.create_with_profile(name="Ada", surname="Lovelace", email="dup@example.com", password="pw-123456")

    with pytest.raises(ValueError, match="already registered"):
        service.create_with_profile(name="Grace", surname="Hopper", email="dup@example.com", password="pw-123456")

    assert UserRepository().count() == 1


def test_create_with_profile_is_atomic_when_the_profile_fails(test_app, clean_database):
    service = AuthenticationService()

    with patch.object(service.user_profile_repository, "create", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError):
            service.create_with_profile(name="Ada", surname="Lovelace", email="ada@example.com", password="pw-123456")

    # The user insert must be rolled back together with the failed profile insert.
    assert UserRepository().count() == 0


def test_enqueue_confirmation_email_delegates_to_the_task_queue(test_app):
    with patch("app.features.auth.services.TaskQueueManager.enqueue_task") as enqueue:
        AuthenticationService().enqueue_confirmation_email("ada@example.com")

    enqueue.assert_called_once_with(CONFIRMATION_EMAIL_TASK, email="ada@example.com", timeout=10)
