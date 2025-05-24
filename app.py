from flask import Flask, render_template, redirect, url_for, request, session
from flask_admin import Admin, AdminIndexView, expose
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, BadSignature
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user
from models import db, Studente, Slot, StatoPrenotazione, TipoEvento, Ricorrenza, TipoSlot
from views import create_admin
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import os

load_dotenv()  # carica variabili dal file .env

ADMIN_MAIL = os.getenv("ADMIN_MAIL")
ADMIN_USR = os.getenv("ADMIN_USR")
ADMIN_PWD = os.getenv("ADMIN_PWD")
ERROR_MSG = "Credenziali scadute, effettuare nuovamente l'accesso"
CONFERMA_MSG = "Prenotazione effettuata"
DISDETTA_MSG = "Prenotazione annullata"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///srm.db"
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)

# Configurazione Mail
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT"))
app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS") == "True"
app.config['MAIL_USE_SSL'] = os.getenv("MAIL_USE_SSL") == "True"
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)
db.init_app(app)

scheduler = BackgroundScheduler()
scheduler.start()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "admin_login"

class AdminUser(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return AdminUser(id="admin")
    return None

class AdminHomeView(AdminIndexView):
    @expose("/")
    def admin_home(self):
        next_week = datetime.now() + timedelta(days=7)
        prenotati = Slot.query.filter(
            Slot.inizio <= next_week,
            Slot.stato == "PRENOTATO"
        ).order_by(Slot.inizio).all()
        ricevimenti = [slot for slot in prenotati if slot.tipo == TipoEvento.RICEVIMENTO]
        esami = [slot for slot in prenotati if slot.tipo == TipoEvento.ESAME]
        tirocini = [slot for slot in prenotati if slot.tipo == TipoEvento.TIROCINIO]

        return self.render("admin/admin_home.html", ric=ricevimenti, esm=esami, tir=tirocini)


admin = Admin(name="SRM", template_mode="bootstrap4", index_view=AdminHomeView())
admin.init_app(app)
create_admin(admin, db)


@app.route("/admin")
@login_required
def admin_home_view():
    if current_user.id == "admin":
        return redirect(url_for("admin.admin_home"))
    else:
        return redirect(url_for("admin_login"))


@app.route("/admin_login/<token>", methods=["GET", "POST"])
def admin_login(token):
    try:
        email = serializer.loads(token, salt="ADMIN-accesso-confermato")
    except BadSignature:
        return "Token di accesso non valido"

    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        remember = "rememberMe" in request.form

        if username == ADMIN_USR and password == ADMIN_PWD:
            admin_user = AdminUser(id="admin")
            login_user(admin_user, remember=remember)
            return redirect(url_for("admin_home_view"))
        else:
            error = "Credenziali non valide"

    return render_template("admin/admin_login.html", token=token, error=error)


@app.route("/")
def index():
    message = request.args.get("error")
    return render_template("index.html", error=message)


@app.route("/confirm", methods=["POST"])
def confirm():
    email = request.form["email"]
    if email == ADMIN_MAIL:
        token = serializer.dumps(email, salt="ADMIN-accesso-confermato")
        admin_otp = url_for("admin_login", token=token, _external=True)
        html = render_template("admin/admin_email.html", otp=admin_otp)
        msg = Message(
            subject="Accesso amministrativo confermato",
            recipients=[email],
            html=html
        )
    else:
        token = serializer.dumps(email, salt="email-accesso-confermata")
        otp = url_for("login", token=token, _external=True)
        html = render_template("email.html", otp=otp)

        msg = Message(
            subject="Conferma accesso",
            recipients=[email],
            html=html
        )
    mail.send(msg)

    return render_template("confirm.html")


@app.route("/login/<token>", methods=["GET", "POST"])
def login(token):
    try:
        email = serializer.loads(token, salt="email-accesso-confermata", max_age=900)
    except BadSignature:
        return "Token di accesso scaduto o non valido"

    if request.method == "POST":
        matricola = request.form["matricola"]
        nome = request.form["nome"]
        cognome = request.form["cognome"]
        mail = request.form["email"]

        session["matricola"] = matricola
        session["nome"] = nome
        session["cognome"] = cognome
        session["mail"] = mail

        studente = Studente.query.filter_by(
            matricola=matricola,
            nome=nome,
            cognome=cognome,
            mail=mail
        ).first()

        if not studente:
            studente = Studente(
                matricola=matricola,
                nome=nome,
                cognome=cognome,
                mail=mail
            )
            db.session.add(studente)
            db.session.commit()

        session["studente_id"] = studente.id
        session.permanent = True
        return redirect(url_for("home"))

    return render_template("login.html", email=email, token=token)


@app.route("/home")
def home():
    studente_id = session.get("studente_id")
    if not studente_id:
        return redirect(url_for("index", error=ERROR_MSG))
    studente = Studente.query.filter_by(
        id=session["studente_id"]
    ).first()
    permessi = studente.permessi.split(',')

    ric = "RIC" in permessi
    esm = "ESM" in permessi
    tir = "TIR" in permessi

    error = request.args.get("error")
    return render_template("home.html", r=ric, e=esm, t=tir, error=error)


@app.route("/slots")
def slots():
    tipo = request.args["tipo"]
    start_date = datetime.now() + timedelta(days=2)

    # controllo tipo di slot
    multiSlot = False
    primo_slot = Slot.query.filter(
        Slot.tipo == tipo,
        Slot.inizio >= start_date,
        Slot.stato == "ATTIVO"
    ).order_by(Slot.inizio).first()
    if primo_slot:
        ricorrenza = Ricorrenza.query.get(primo_slot.ricorrenza_id)
        if ricorrenza.tipoSlot == TipoSlot.MULTISLOT:
            multiSlot = True

    # controllo limite massimo prenotazioni
    count = Slot.query.filter_by(
        tipo=tipo,
        studente_id=session.get("studente_id")
    ).count()

    if tipo == "ESAME":
        disableb = count >= 1
    else:
        disableb = count >= 3

    slot = get_slots(multiSlot, start_date, tipo)
    return render_template("slots.html", slots=slot, tipo=tipo, dis=disableb)

def get_slots(multiSlot, start_date, tipo):
    if multiSlot:
        slots = []
        date = start_date
        giorni = 0
        slot_disponibili = True

        while giorni < 3 and slot_disponibili:
            s = Slot.query.filter(
                Slot.tipo == tipo,
                Slot.inizio >= date,
                Slot.stato == "ATTIVO"
            ).order_by(Slot.inizio).first()

            if s:
                slots.append(s)
                giorni += 1
                date = s.inizio + timedelta(days=1)
            else:
                slot_disponibili = False

        return slots
    else:
        return Slot.query.filter(
            Slot.tipo == tipo,
            Slot.inizio >= start_date,
            Slot.stato == "ATTIVO"
        ).order_by(Slot.inizio).limit(10).all()


@app.route("/prenota/<int:slot_id>", methods=["GET"])
def prenota(slot_id):
    studente_id = session.get("studente_id")
    if not studente_id:
        return redirect(url_for("index", error=ERROR_MSG))

    try:
        with db.session.begin():  # Avvia una transazione
            slot = db.session.query(Slot).filter(Slot.id == slot_id).with_for_update().first()

            if not slot or slot.stato != StatoPrenotazione.ATTIVO:
                return redirect(url_for("home", error="Lo slot selezionato è già stato prenotato"))

            slot.studente_id = studente_id
            slot.stato = StatoPrenotazione.PRENOTATO
            db.session.commit()  # Conferma la transazione

        return redirect(url_for("profile", msg=CONFERMA_MSG))

    except SQLAlchemyError:
        db.session.rollback()  # In caso di errore, annulla la transazione
        return redirect(url_for("home", error="Lo slot selezionato è già stato prenotato"))


@app.route("/profile")
def profile():
    studente_id = session.get("studente_id")
    if not studente_id:
        return redirect(url_for("index", error=ERROR_MSG))

    attive = Slot.query.filter_by(
        studente_id=studente_id,
        stato=StatoPrenotazione.PRENOTATO
    ).all()

    for slot in attive:
        slot.disdici = (slot.inizio - datetime.now()) > timedelta(days=1)

    concluse = Slot.query.filter_by(
        studente_id=studente_id,
        stato=StatoPrenotazione.CONCLUSO
    ).all()

    msg = request.args.get("msg")
    return render_template("profile.html", p_attive=attive, p_concluse=concluse, msg=msg)


@app.route("/disdici/<int:slot_id>", methods=["POST"])
def disdici(slot_id):
    studente_id = session.get("studente_id")
    if not studente_id:
        return redirect(url_for("index", error=ERROR_MSG))

    slot = Slot.query.filter_by(
        id=slot_id,
        studente_id=studente_id,
        stato=StatoPrenotazione.PRENOTATO
    ).first()

    if slot:
        slot.stato = StatoPrenotazione.ATTIVO
        slot.studente_id = None
        db.session.commit()

    return redirect(url_for("profile", msg=DISDETTA_MSG))


with app.app_context():
    db.create_all()

#Funzione per aggiornamento stato slots
def update_stato_slot():
    with app.app_context():
        now = datetime.now()
        slots = Slot.query.filter(
            Slot.stato != StatoPrenotazione.CONCLUSO,
            Slot.fine < now
        ).all()
        for slot in slots:
            slot.stato = StatoPrenotazione.CONCLUSO
        db.session.commit()

#Funzioni per invio di notifiche
def send_reminder():
    with app.app_context():
        time = datetime.now() + timedelta(hours=24)
        slots = Slot.query.filter(
            Slot.stato == StatoPrenotazione.PRENOTATO,
            Slot.inizio >= time,
            Slot.inizio < time + timedelta(minutes=1)
        ).all()

        for slot in slots:
            studente = Studente.query.get(slot.studente_id)
            if studente:
                send_email(studente.mail, slot.inizio)
                send_email(ADMIN_MAIL, slot.inizio)

def send_email(dest, inizio):
    date = inizio.strftime('%d/%m/%Y')
    time = inizio.strftime('%H:%M')
    reminder = render_template("reminder.html", date=date, time=time)
    msg = Message(
        subject="Promemoria appuntamento",
        recipients=[dest],
        html=reminder
    )
    mail.send(msg)

scheduler.add_job(func=update_stato_slot, trigger="interval", minutes=1)
scheduler.add_job(func=send_reminder, trigger="interval", minutes=1)

app.run()