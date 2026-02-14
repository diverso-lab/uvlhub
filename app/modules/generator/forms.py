from flask_wtf import FlaskForm
from wtforms import SubmitField


class GeneratorForm(FlaskForm):
    submit = SubmitField('Save generator')
