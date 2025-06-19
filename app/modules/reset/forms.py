from flask_wtf import FlaskForm
from wtforms import SubmitField


class ResetForm(FlaskForm):
    submit = SubmitField("Save reset")
