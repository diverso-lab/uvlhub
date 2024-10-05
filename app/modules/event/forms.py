from flask_wtf import FlaskForm
from wtforms import SubmitField


class EventForm(FlaskForm):
    submit = SubmitField('Save event')
