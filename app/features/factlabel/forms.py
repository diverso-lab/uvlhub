from flask_wtf import FlaskForm
from wtforms import SubmitField


class FactlabelForm(FlaskForm):
    submit = SubmitField("Save factlabel")
