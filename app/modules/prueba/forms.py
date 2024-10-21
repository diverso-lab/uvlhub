from flask_wtf import FlaskForm
from wtforms import SubmitField


class PruebaForm(FlaskForm):
    submit = SubmitField('Save prueba')
