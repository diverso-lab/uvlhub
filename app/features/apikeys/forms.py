from flask_wtf import FlaskForm
from wtforms import SubmitField


class ApikeysForm(FlaskForm):
    submit = SubmitField("Save apikeys")
