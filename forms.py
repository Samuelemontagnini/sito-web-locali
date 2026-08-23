from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Accedi')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Conferma Password', validators=[DataRequired(), EqualTo('password', message='Le password devono combaciare')])
    submit = SubmitField('Registrati')

class EventForm(FlaskForm):
    titolo = StringField('Titolo', validators=[DataRequired()])
    descrizione = TextAreaField('Descrizione', validators=[DataRequired()])
    data = StringField('Data (es. 25/08/2026)', validators=[DataRequired()])
    orario = StringField('Orario (es. 22:30)', validators=[DataRequired()])
    indirizzo = StringField('Indirizzo Completo (es. Piazza della Loggia, Brescia)', validators=[DataRequired()])
    # Nuovo campo file per caricare l'immagine dal computer (accetta solo jpg, png, jpeg)
    immagine = FileField('Carica Immagine', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Solo immagini!')])
    submit = SubmitField('Pubblica Evento')