import os

import requests
from app.modules.recaptcha.repositories import RecaptchaRepository
from core.services.BaseService import BaseService


class RecaptchaService(BaseService):
    def __init__(self):
        super().__init__(RecaptchaRepository())

    def validate_recaptcha(self, response):
        secret = os.getenv('GOOGLE_RECAPTCHA_SECRET_KEY')
        payload = {
            'secret': secret,
            'response': response
        }
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
        result = response.json()
        return result.get('success')
