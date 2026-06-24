from unittest.mock import MagicMock, patch

import pytest
from itsdangerous import SignatureExpired

from app.features.auth.services import AuthenticationService
from app.features.confirmemail.services import ConfirmemailService, EmailConfirmationError

pytestmark = pytest.mark.service


def _register(email):
    return AuthenticationService().create_with_profile(name="Test", surname="User", email=email, password="pw-123456")


def test_token_round_trip_activates_the_user(test_app, clean_database):
    _register("confirm@example.com")
    service = ConfirmemailService()
    token = service.get_token_from_email("confirm@example.com")

    user = service.confirm_user_with_token(token)

    assert user.email == "confirm@example.com"
    assert user.active is True


def test_tampered_token_raises_a_confirmation_error(test_app, clean_database):
    service = ConfirmemailService()

    with pytest.raises(EmailConfirmationError, match="invalid"):
        service.confirm_user_with_token("clearly-not-a-valid-token")


def test_expired_token_raises_a_confirmation_error(test_app, clean_database):
    service = ConfirmemailService()
    serializer = MagicMock()
    serializer.loads.side_effect = SignatureExpired("expired")

    with patch.object(service, "get_serializer", return_value=serializer):
        with pytest.raises(EmailConfirmationError, match="expired"):
            service.confirm_user_with_token("whatever")


def test_token_for_unknown_email_raises_value_error(test_app, clean_database):
    service = ConfirmemailService()
    token = service.get_token_from_email("ghost@example.com")

    with pytest.raises(ValueError, match="No account"):
        service.confirm_user_with_token(token)
