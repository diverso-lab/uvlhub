from flask_wtf import FlaskForm
from wtforms import SubmitField


class OrcidForm(FlaskForm):
    submit = SubmitField("Save orcid")
