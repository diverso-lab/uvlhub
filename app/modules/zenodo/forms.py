from flask_wtf import FlaskForm
from wtforms import SubmitField


class ZenodoForm(FlaskForm):
    submit = SubmitField("Save zenodo")
