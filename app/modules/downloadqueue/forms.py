from flask_wtf import FlaskForm
from wtforms import SubmitField


class DownloadqueueForm(FlaskForm):
    submit = SubmitField("Save downloadqueue")
