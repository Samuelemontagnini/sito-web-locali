from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False) # Solo gli admin possono aggiungere eventi

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(100), nullable=False)
    descrizione = db.Column(db.Text, nullable=False)
    data = db.Column(db.String(20), nullable=False)
    orario = db.Column(db.String(20), nullable=False)
    indirizzo = db.Column(db.String(150), nullable=False)
    latitudine = db.Column(db.Float, nullable=False)
    longitudine = db.Column(db.Float, nullable=False)
    immagine = db.Column(db.String(250), nullable=False)