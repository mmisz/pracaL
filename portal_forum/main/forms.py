from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, ValidationError
from wtforms.fields import html5 as h5fields
from wtforms.widgets import html5 as h5widgets


def validate_year(form, date_release):
    year = int(datetime.utcnow().year)

    if date_release.data < 1973:
        raise ValidationError('Podano zły rok.')
    elif date_release.data > year:
        raise ValidationError('Podano zły rok.')

class AlbumForm(FlaskForm):
    title = StringField('Nazwa albumu', validators=[DataRequired()])
    date_release = h5fields.IntegerField("Rok wydania", [validate_year])
    description = TextAreaField('Opis')



