from flask_wtf import FlaskForm
from wtforms import SubmitField


class ExploreForm(FlaskForm):
    submit = SubmitField("Submit")
