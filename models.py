from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from enum import Enum
from datetime import datetime, timedelta

from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY


db = SQLAlchemy();


SLOT = timedelta(minutes=30)    #durata di ogni slot

class TipoEvento(Enum):
    RICEVIMENTO = "Ricevimento"
    ESAME = "Esame"
    TIROCINIO = "Tirocinio"

class StatoPrenotazione(Enum):
    ATTIVO = "Attivo"
    PRENOTATO = "Prenotato"
    CONCLUSO = "Concluso"

class Frequenze(Enum):
    GIORNALIERA = "Ogni giorno"
    SETTIMANALE = "Ogni settimana"
    MENSILE = "Ogni mese"

class TipoSlot(Enum):
    SINGOLO = "Singolo"
    MULTISLOT = "Multi-Slot"


class Studente(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    matricola = db.Column(db.String(6), nullable=False)
    nome = db.Column(db.String(50), nullable=False)
    cognome = db.Column(db.String(50), nullable=False)
    mail = db.Column(db.String(100), unique=True, nullable=False)
    permessi = db.Column(db.String, nullable = False, default = "RIC")

    @property
    def set_permessi(self):
        if self.permessi:
            return set(self.permessi.split(','))
        return set()

    @set_permessi.setter
    def set_permessi(self, value):
        self.permessi = ','.join(sorted(value))

    def __str__(self):
        return self.nome + " " + self.cognome + " (" + self.matricola + ")"


class Evento(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    tipo = db.Column(db.Enum(TipoEvento), nullable = False)
    tipoSlot = db.Column(db.Enum(TipoSlot), nullable = False)
    inizio = db.Column(db.DateTime, nullable = False)
    fine = db.Column(db.DateTime, nullable = False)
    frequenza = db.Column(db.Enum(Frequenze), nullable = False)
    count = db.Column(db.Integer, default = None)
    until = db.Column(db.DateTime, default = None) 

    def set_rrule(self): 
        freq_map = {
            "GIORNALIERA": DAILY,
            "SETTIMANALE": WEEKLY,
            "MENSILE": MONTHLY
        }
        freq = freq_map.get(self.frequenza)
        dtstart = self.inizio
        count = self.count if self.count else None
        until = self.until if self.until else None
        
        return rrule(freq=freq, dtstart=dtstart, count=count, until=until)


class Ricorrenza(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    tipo = db.Column(db.Enum(TipoEvento), nullable = False)
    tipoSlot = db.Column(db.Enum(TipoSlot), nullable = False)
    inizio = db.Column(db.DateTime, nullable = False)
    fine = db.Column(db.DateTime, nullable = False)
    evento_id = db.Column(db.Integer, db.ForeignKey("evento.id"), nullable = True)
    evento = db.relationship("Evento", backref = db.backref("ricorrenze", cascade = "all, delete-orphan"))

@event.listens_for(db.session, "after_flush")
def after_flush(session, flush_context):
    for target in session.new:      #dopo insert
        if isinstance(target, Evento):
            create_rec(session, target)

def create_rec(session, target):
    key = target.id
    tipo_evento = target.tipo
    tipo_slot = target.tipoSlot
    dates = target.set_rrule()
    for d in dates:
        ricorrenza = Ricorrenza(
            tipo=tipo_evento,
            tipoSlot = tipo_slot,
            inizio=d,
            fine=d + (target.fine - target.inizio),
            evento_id=key
        )
        session.add(ricorrenza)


class Slot(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    tipo = db.Column(db.Enum(TipoEvento), nullable = False)
    inizio = db.Column(db.DateTime, nullable = False)
    fine = db.Column(db.DateTime, nullable = False)
    stato = db.Column(db.Enum(StatoPrenotazione), nullable = False, default = StatoPrenotazione.ATTIVO)
    note = db.Column(db.Text)
    ricorrenza_id = db.Column(db.Integer, db.ForeignKey("ricorrenza.id"), nullable = False)
    studente_id = db.Column(db.Integer, db.ForeignKey("studente.id", ondelete = "SET NULL"), nullable = True)
    ricorrenza = db.relationship("Ricorrenza", backref=db.backref("slots", cascade="all, delete-orphan"))
    studente = db.relationship("Studente", backref=db.backref("slots", cascade="save-update"))

@event.listens_for(Ricorrenza, "after_insert")
def slot_after_insert(mapper, connection, target):
    create_slot(db.session, target)

def create_slot(session, ricorrenza):
    dtstart = ricorrenza.inizio
    while(dtstart + SLOT <= ricorrenza.fine):
        slot = Slot(
            tipo = ricorrenza.tipo,
            inizio = dtstart,
            fine = dtstart + SLOT,
            stato = StatoPrenotazione.ATTIVO,
            note = None,
            ricorrenza_id = ricorrenza.id,
            studente_id = None
        )
        dtstart += SLOT
        session.add(slot)
