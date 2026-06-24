import pytest

from app.features.webhook.services import WebhookService

pytestmark = pytest.mark.unit


def test_is_authorized_accepts_the_matching_bearer_token(monkeypatch):
    monkeypatch.setenv("WEBHOOK_TOKEN", "s3cr3t")

    assert WebhookService().is_authorized("Bearer s3cr3t") is True


def test_is_authorized_rejects_a_wrong_token(monkeypatch):
    monkeypatch.setenv("WEBHOOK_TOKEN", "s3cr3t")

    assert WebhookService().is_authorized("Bearer wrong") is False


def test_is_authorized_rejects_a_missing_header(monkeypatch):
    monkeypatch.setenv("WEBHOOK_TOKEN", "s3cr3t")

    assert WebhookService().is_authorized(None) is False


def test_is_authorized_rejects_when_no_token_is_configured(monkeypatch):
    monkeypatch.delenv("WEBHOOK_TOKEN", raising=False)

    assert WebhookService().is_authorized("Bearer anything") is False
