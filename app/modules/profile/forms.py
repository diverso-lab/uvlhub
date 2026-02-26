from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class UserProfileForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    surname = StringField(
        "Surname",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )

    affiliation = StringField(
        "Affiliation",
        validators=[
            Optional(),
            Length(min=5, max=100),
        ],
    )
    submit = SubmitField("Save profile")
