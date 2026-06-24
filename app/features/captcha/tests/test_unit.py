import pytest

from app.features.captcha.services import ALLOWED_CHARACTERS, CaptchaService

pytestmark = pytest.mark.unit


def test_generate_captcha_text_has_the_default_length():
    assert len(CaptchaService().generate_captcha_text()) == 6


def test_generate_captcha_text_honours_a_custom_length():
    assert len(CaptchaService().generate_captcha_text(10)) == 10


def test_generate_captcha_text_uses_only_allowed_characters():
    text = CaptchaService().generate_captcha_text(50)

    assert set(text) <= set(ALLOWED_CHARACTERS)


def test_allowed_characters_exclude_ambiguous_glyphs():
    assert not set("O0I1") & set(ALLOWED_CHARACTERS)
