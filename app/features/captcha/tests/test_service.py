import pytest
from flask import session

from app.features.captcha.services import SESSION_KEY, CaptchaService

pytestmark = pytest.mark.service


def test_generate_captcha_stores_text_and_returns_a_data_uri(test_app):
    with test_app.test_request_context():
        data_uri = CaptchaService().generate_captcha()

        assert data_uri.startswith("data:image/png;base64,")
        assert session[SESSION_KEY]


def test_validate_captcha_accepts_the_stored_value(test_app):
    with test_app.test_request_context():
        service = CaptchaService()
        service.generate_captcha()

        assert service.validate_captcha(session[SESSION_KEY]) is True


def test_validate_captcha_rejects_a_wrong_value(test_app):
    with test_app.test_request_context():
        service = CaptchaService()
        service.generate_captcha()

        assert service.validate_captcha("definitely-wrong") is False


def test_validate_captcha_is_false_without_a_generated_captcha(test_app):
    with test_app.test_request_context():
        assert CaptchaService().validate_captcha("anything") is False
