import pytest
from app import app as APP
from models import db, Studente, Evento, Ricorrenza, Slot, TipoEvento, TipoSlot, Frequenze
from datetime import datetime, timedelta

@pytest.fixture
def app():
    app = APP
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

def test_add_studente(client):
    new = Studente(
                matricola = "abc123",
                nome = "nome",
                cognome = "cognome",
                mail = "mail@test.it"
            )
    db.session.add(new)
    db.session.commit()

    studente = Studente.query.filter_by(matricola="abc123").first()
    assert studente is not None
    assert studente.nome == "nome"
    assert studente.cognome == "cognome"
    assert studente.mail == "mail@test.it"
    assert studente.permessi == "RIC"

def test_add_event(client):
    start = datetime.now()
    end = start + timedelta(hours=1)

    new = Evento(
        tipo = "RICEVIMENTO",
        tipoSlot = "SINGOLO",
        inizio = start,
        fine = end,
        frequenza = "GIORNALIERA",
        count = 5,
        until = None
    )
    db.session.add(new)
    db.session.commit()

    evento = Evento.query.filter_by(inizio=start).first()
    assert evento is not None

    ricorrenze = Ricorrenza.query.filter_by(evento_id=evento.id).all()
    assert len(ricorrenze) == 5

    for r in ricorrenze:
        slots = Slot.query.filter_by(ricorrenza_id=r.id).all()
        assert len(slots) == 2

    db.session.delete(evento)
    db.session.commit()

    assert Evento.query.count() == 0
    assert Ricorrenza.query.count() == 0
    assert Slot.query.count() == 0

def test_add_ricorrenza(client):
    start = datetime.now()
    end = start + timedelta(hours=2)

    new = Ricorrenza(
        tipo = "RICEVIMENTO",
        tipoSlot = "SINGOLO",
        inizio = start,
        fine = end
    )
    db.session.add(new)
    db.session.commit()

    ric = Ricorrenza.query.filter_by(inizio=start).first()
    assert ric is not None
    
    slots = Slot.query.filter_by(ricorrenza_id=ric.id).all()
    assert len(slots) == 4