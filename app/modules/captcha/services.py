import base64
import random
from io import BytesIO

from captcha.image import ImageCaptcha
from flask import session
from PIL import Image


class CaptchaService:
    def __init__(self):
        self.image_captcha = ImageCaptcha()

    def generate_captcha_text(self, length=6) -> str:
        allowed_characters = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        return "".join(random.choice(allowed_characters) for _ in range(length))

    def generate_captcha(self):
        captcha_text = self.generate_captcha_text()
        session["captcha_text"] = captcha_text
        data = self.image_captcha.generate(captcha_text)
        image = Image.open(data)
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"

    def validate_captcha(self, user_input):
        return user_input == session.get("captcha_text")
