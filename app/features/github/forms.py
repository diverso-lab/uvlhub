from flask_wtf import FlaskForm
from wtforms import SubmitField


class GithubForm(FlaskForm):
    submit = SubmitField("Save github")
