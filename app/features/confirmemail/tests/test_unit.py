import pytest

from app.features.confirmemail.services import EmailConfirmationError

pytestmark = pytest.mark.unit


def test_email_confirmation_error_is_an_exception():
    assert issubclass(EmailConfirmationError, Exception)


def test_email_confirmation_error_preserves_its_message():
    error = EmailConfirmationError("The confirmation link has expired.")

    assert str(error) == "The confirmation link has expired."
