from flask_wtf import FlaskForm
from wtforms import SubmitField


class FlamapyForm(FlaskForm):
    submit = SubmitField("Save flamapy")
