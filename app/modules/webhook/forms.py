from flask_wtf import FlaskForm
from wtforms import SubmitField


class WebhookForm(FlaskForm):
    submit = SubmitField("Save webhook")
