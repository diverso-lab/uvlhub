from flask_wtf import FlaskForm
from wtforms import SubmitField


class MailForm(FlaskForm):
    submit = SubmitField("Save mail")
