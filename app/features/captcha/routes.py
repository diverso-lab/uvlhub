from app.features.captcha import captcha_bp
from app.features.captcha.services import CaptchaService

captcha_service = CaptchaService()


@captcha_bp.route("/captcha/generate")
def generate_captcha():
    return captcha_service.generate_captcha()
