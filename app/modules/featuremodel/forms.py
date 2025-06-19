from flask_wtf import FlaskForm
from wtforms import SubmitField


class FeaturemodelForm(FlaskForm):
    submit = SubmitField("Save featuremodel")
