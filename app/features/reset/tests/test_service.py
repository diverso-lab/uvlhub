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
