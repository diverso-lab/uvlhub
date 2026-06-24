from flask_wtf import FlaskForm
from wtforms import SubmitField


class CaptchaForm(FlaskForm):
    submit = SubmitField("Save recaptcha")
