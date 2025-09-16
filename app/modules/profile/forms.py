from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Regexp


class UserProfileForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    surname = StringField("Surname", validators=[DataRequired(), Length(max=100)])
    orcid = StringField(
        "ORCID",
        validators=[
            Optional(),
            Length(min=19, max=19, message="ORCID must have 16 numbers separated by dashes"),
            Regexp(r"^\d{4}-\d{4}-\d{4}-\d{4}$", message="Invalid ORCID format"),
        ],
    )
    affiliation = StringField("Affiliation", validators=[Optional(), Length(min=5, max=100)])
    submit = SubmitField("Save profile")
