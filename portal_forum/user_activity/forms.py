from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, widgets, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, ValidationError
from wtforms.fields import html5 as h5fields
from wtforms.widgets import html5 as h5widgets
from portal_forum.models import Album

class ThreadForm(FlaskForm):
    topic = StringField('Temat wątku', validators=[DataRequired()])
    description = TextAreaField('Opis')
    
class PostForm(FlaskForm):
    reply = TextAreaField('Odpowiedź')

class TrackForm(FlaskForm):
    title = StringField('Tytuł', validators=[DataRequired()])
    date_release = h5fields.IntegerField("Rok wydania", widget=h5widgets.NumberInput())
    lyrics = TextAreaField('Tekst', validators=[DataRequired()])
    description = TextAreaField('Opis utworu')
    lyrics_by = StringField('Autor tekstu')
    '''(Proteza)
    <div class="form-group">
                        <label class="form-control-label">
                            Albumy
                        </label>
                    <table>
                        {% for album in albums %}
                            <tr>
                                <td><input type="checkbox" name="albums" value="{{ album.id }}"></td>
                                <td> {{ album.title }} ({{ album.date_release }})</td>
                            </tr>

                        {% endfor %}
                    </table>
                    </div>
    '''
def validate_scrap(form, scrap_description):

    if len(scrap_description.data) < 2:
        raise ValidationError('Oznaczono za krótki fragment.')

class ScrapForm(FlaskForm):
    scrap_description = TextAreaField('Fragment', [validate_scrap])
    scrap_text = HiddenField("scrap-text", validators=[DataRequired()])
