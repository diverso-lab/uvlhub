from unittest.mock import patch

import pytest
from werkzeug.exceptions import NotFound

from app.features.auth.repositories import UserRepository
from app.features.reset.repositories import ResetRepository
from app.features.reset.services import ResetService

pytestmark = pytest.mark.service


def test_add_token_is_idempotent(test_app, clean_database):
    service = ResetService()
    service.add_token("tok-1")
    service.add_token("tok-1")

    assert ResetRepository().count() == 1


def test_add_token_ignores_none(test_app, clean_database):
    ResetService().add_token(None)

    assert ResetRepository().count() == 0


def test_token_already_used_tracks_state(test_app, clean_database):
    service = ResetService()
    service.add_token("tok-1")

    assert service.token_already_used("tok-1") is False

    service.mark_token_as_used("tok-1")
    assert service.token_already_used("tok-1") is True


def test_reset_password_changes_the_hash(test_app, clean_database):
    UserRepository().create(email="reset@example.com", password="old-password")

    ResetService().reset_password("reset@example.com", "new-password-1")

    user = UserRepository().get_by_email("reset@example.com")
    assert user.check_password("new-password-1") is True


def test_reset_password_for_unknown_email_raises(test_app, clean_database):
    with pytest.raises(ValueError, match="No account"):
        ResetService().reset_password("ghost@example.com", "whatever-1")


def test_check_valid_token_aborts_on_a_tampered_token(test_app):
    with pytest.raises(NotFound):
        ResetService().check_valid_token("clearly-not-a-valid-token")


def test_send_reset_password_mail_returns_none_for_unknown_email(test_app, clean_database):
    with patch("app.features.reset.services.TaskQueueManager.enqueue_task") as enqueue:
        assert ResetService().send_reset_password_mail("ghost@example.com") is None

    enqueue.assert_not_called()


def test_send_reset_password_mail_uses_the_stored_address(test_app, clean_database):
    """The link goes to the account's own address, never to what was typed.

    The database collation treats different spellings of an address as equal,
    so the typed text can match an account it does not belong to.
    """
    UserRepository().create(email="owner@example.com", password="old-password")
    service = ResetService()

    with patch("app.features.reset.services.TaskQueueManager.enqueue_task") as enqueue:
        token = service.send_reset_password_mail("OWNER@example.com")

    assert token is not None
    assert enqueue.call_args.kwargs["email"] == "owner@example.com"
    assert service.get_email_by_token(token) == "owner@example.com"


def test_reset_password_only_accepts_the_stored_spelling(test_app, clean_database):
    # Tokens carry the stored address. One signed for another spelling (issued
    # before that was the case) must not change the password of the account.
    UserRepository().create(email="owner2@example.com", password="old-password")
    service = ResetService()

    with pytest.raises(ValueError):
        service.reset_password("OWNER2@example.com", "new-password-1")

    assert UserRepository().get_by_email("owner2@example.com").check_password("old-password")


def test_reset_and_notify_notifies_the_stored_address(test_app, clean_database):
    UserRepository().create(email="owner3@example.com", password="old-password")
    service = ResetService()
    service.add_token("tok-3")

    with patch("app.features.reset.services.TaskQueueManager.enqueue_task") as enqueue:
        service.reset_and_notify(email="owner3@example.com", password="new-password-1", token="tok-3")

    assert enqueue.call_args.kwargs["email"] == "owner3@example.com"
    assert service.token_already_used("tok-3") is True
