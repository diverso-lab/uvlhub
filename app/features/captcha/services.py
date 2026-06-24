import base64
import secrets
from io import BytesIO

from captcha.image import ImageCaptcha
from flask import session
from PIL import Image

# Visually unambiguous alphabet: no O/0, I/1 lookalikes.
ALLOWED_CHARACTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
SESSION_KEY = "captcha_text"


class CaptchaService:
    def __init__(self):
        self.image_captcha = ImageCaptcha()

    def generate_captcha_text(self, length: int = 6) -> str:
        return "".join(secrets.choice(ALLOWED_CHARACTERS) for _ in range(length))

    def generate_captcha(self) -> str:
        captcha_text = self.generate_captcha_text()
        session[SESSION_KEY] = captcha_text
        data = self.image_captcha.generate(captcha_text)
        image = Image.open(data)
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"

    def validate_captcha(self, user_input) -> bool:
        expected = session.get(SESSION_KEY)
        return bool(expected) and user_input == expected
