from flask_wtf import FlaskForm
from wtforms import SubmitField


class ElasticsearchForm(FlaskForm):
    submit = SubmitField("Save elasticsearch")
