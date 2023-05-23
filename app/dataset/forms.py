from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FieldList, FormField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, URL, Optional
from enum import Enum

from .models import PublicationType


class AuthorForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    affiliation = StringField('Affiliation')
    orcid = StringField('ORCID')
    gnd = StringField('GND')


class DataSetForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    publication_type = SelectField('Publication type',
                                   choices=[(pt.value, pt.name.replace('_', ' ').title()) for pt in PublicationType],
                                   validators=[DataRequired()])

    publication_doi = StringField('Publication DOI', validators=[Optional(), URL()])
    dataset_doi = StringField('Dataset DOI', validators=[Optional(), URL()])
    tags = StringField('Tags (separated by commas)')
    authors = FieldList(FormField(AuthorForm))
    submit = SubmitField('Submit')

