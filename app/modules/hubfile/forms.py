from flask_wtf import FlaskForm
from wtforms import SubmitField


class HubfileForm(FlaskForm):
    submit = SubmitField("Save hubfile")
