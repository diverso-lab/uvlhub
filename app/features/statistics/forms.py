from flask_wtf import FlaskForm
from wtforms import SubmitField


class StatisticsForm(FlaskForm):
    submit = SubmitField("Save statistics")
