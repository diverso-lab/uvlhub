from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import DataRequired


class DataSetForm(FlaskForm):
    user_id = IntegerField('User ID', validators=[DataRequired()])
    meta_data_id = IntegerField('Meta Data ID', validators=[DataRequired()])
    submit = SubmitField('Create DataSet')
