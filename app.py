import os
import secrets
from flask import Flask, render_template, redirect, url_for, flash, request
from models import db, User, Event
from forms import LoginForm, EventForm, RegisterForm
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_bcrypt import Bcrypt

# Directory di base per un salvataggio sicuro e stabile del database
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chiave_super_segreta_12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'database.db')

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Funzione per salvare l'immagine caricata dal computer nella cartella static/uploads
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    
    upload_dir = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    picture_path = os.path.join(upload_dir, picture_fn)
    form_picture.save(picture_path)
    return picture_fn

# --- ROTTA PRINCIPALE & RICERCA ---
@app.route('/')
def index():
    q = request.args.get('q')
    data_ricerca = request.args.get('data')
    orario_ricerca = request.args.get('orario')

    query = Event.query
    if q:
        query = query.filter((Event.indirizzo.ilike(f'%{q}%')) | (Event.titolo.ilike(f'%{q}%')))
    if data_ricerca:
        parts = data_ricerca.split('-')
        if len(parts) == 3:
            data_formattata = f"{parts[2]}/{parts[1]}/{parts[0]}"
            query = query.filter_by(data=data_formattata)

    eventi_db = query.all()
    eventi = []
    
    for evento in eventi_db:
        if orario_ricerca:
            try:
                ora = int(evento.orario.split(':')[0])
                if orario_ricerca == 'pomeriggio' and not (12 <= ora < 18): continue
                elif orario_ricerca == 'sera' and not (18 <= ora <= 24): continue
            except:
                pass
                
        # Gestione corretta dei percorsi delle immagini caricate dal PC o link esterni
        if evento.immagine.startswith('http'):
            img_url = evento.immagine
        else:
            img_url = url_for('static', filename='uploads/' + evento.immagine)

        eventi.append({
            "titolo": evento.titolo, 
            "descrizione": evento.descrizione,
            "data": evento.data, 
            "orario": evento.orario, 
            "indirizzo": evento.indirizzo,
            "latitudine": evento.latitudine, 
            "longitudine": evento.longitudine, 
            "immagine": img_url
        })
    return render_template('index.html', eventi=eventi)

# --- AUTENTICAZIONE E REGISTRAZIONE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f'Benvenuto {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login fallito. Email o password errati.', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        user_exist = User.query.filter_by(email=form.email.data).first()
        if user_exist:
            flash('Email già in uso. Prova ad accedere.', 'danger')
            return redirect(url_for('register'))
            
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, is_admin=False)
        db.session.add(user)
        db.session.commit()
        flash('Account creato! Ora puoi effettuare il login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('Sei uscito dal tuo account.', 'success')
    return redirect(url_for('index'))

# --- PANNELLO ADMIN (AGGIUNGI EVENTO TRAMITE MAPPA E FILE) ---
@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
def add_event():
    if not current_user.is_admin:
        flash('Accesso negato. Solo gli admin possono aggiungere eventi.', 'danger')
        return redirect(url_for('index'))
    
    form = EventForm()
    if form.validate_on_submit():
        # Salvataggio del file caricato dal computer
        image_file = save_picture(form.immagine.data)
        
        # Recupero delle coordinate dai campi nascosti scelti cliccando sulla mappa
        lat = float(request.form.get('latitudine', 45.5415))
        lon = float(request.form.get('longitudine', 10.2118))
        
        nuovo_evento = Event(
            titolo=form.titolo.data, 
            descrizione=form.descrizione.data,
            data=form.data.data, 
            orario=form.orario.data, 
            indirizzo=form.indirizzo.data,
            latitudine=lat, 
            longitudine=lon, 
            immagine=image_file
        )
        db.session.add(nuovo_evento)
        db.session.commit()
        flash('Evento pubblicato con successo sulla mappa!', 'success')
        return redirect(url_for('index'))
    return render_template('add_event.html', form=form)

# Inizializzazione automatica database e admin di default
with app.app_context():
    os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
    db.create_all()
    
    if not User.query.filter_by(email='admin@kong.it').first():
        hashed_password = bcrypt.generate_password_hash('Admin123!').decode('utf-8')
        admin = User(username='Admin', email='admin@kong.it', password=hashed_password, is_admin=True)
        db.session.add(admin)
        
        # Eventi iniziali a Brescia
        eventi_brescia = [
            Event(titolo="Aperitivo in Piazza Loggia", descrizione="Fantastico aperitivo nel cuore storico di Brescia.", data="25/08/2026", orario="19:00", indirizzo="Piazza della Loggia, Brescia", latitudine=45.5398, longitudine=10.2185, immagine="https://picsum.photos/seed/brescia1/500/300"),
            Event(titolo="Serata Disco al Molo", descrizione="La migliore musica elettronica con DJ set.", data="26/08/2026", orario="23:30", indirizzo="Via Sorbanella, Brescia", latitudine=45.5255, longitudine=10.1983, immagine="https://picsum.photos/seed/brescia2/500/300"),
            Event(titolo="Concerto in Castello", descrizione="Musica dal vivo con vista panoramica sulla città.", data="28/08/2026", orario="21:00", indirizzo="Castello di Brescia", latitudine=45.5435, longitudine=10.2255, immagine="https://picsum.photos/seed/brescia3/500/300"),
            Event(titolo="Festa sul Lago", descrizione="Beach party al tramonto.", data="30/08/2026", orario="18:00", indirizzo="Desenzano del Garda", latitudine=45.4692, longitudine=10.5335, immagine="https://picsum.photos/seed/brescia4/500/300")
        ]
        db.session.bulk_save_objects(eventi_brescia)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)