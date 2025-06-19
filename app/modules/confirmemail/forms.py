from flask_wtf import FlaskForm
from wtforms import SubmitField


class ConfirmemailForm(FlaskForm):
    submit = SubmitField("Save confirmemail")
