import pytest
from app import app as APP
from models import db, TipoEvento, TipoSlot, Frequenze
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

def test_fine_before_inizio(client):
    inizio = datetime.now()
    fine = inizio - timedelta(hours=1)
    invalid_data = {
        "tipo": TipoEvento.ESAME.name,
        "tipoSlot": TipoSlot.SINGOLO.name,
        "inizio": inizio.strftime("%Y-%m-%d %H:%M:%S"),
        "fine": fine.strftime("%Y-%m-%d %H:%M:%S"),  # Fine prima di inizio
        "frequenza": Frequenze.GIORNALIERA.name,
        "count": 5,
        "until": ''
    }
    response = client.post('/admin/evento/new/', data=invalid_data)
    response_text = response.data.decode('utf-8')
    assert "La data di fine evento deve essere successiva a quella di inizio" in response_text

def test_no_fine_ricorrenza(client):
    inizio = datetime.now()
    fine = inizio + timedelta(hours=1)
    invalid_data = {
        "tipo": TipoEvento.ESAME.name,
        "tipoSlot": TipoSlot.SINGOLO.name,
        "inizio": inizio.strftime("%Y-%m-%d %H:%M:%S"),
        "fine": fine.strftime("%Y-%m-%d %H:%M:%S"),
        "frequenza": Frequenze.GIORNALIERA.name,
        "count": None,
        "until": None                                #Nessuna opzione per termine specificata
    }
    response = client.post('/admin/evento/new/', data=invalid_data)
    response_text = response.data.decode('utf-8')
    assert "Specificare almeno un termine per la ricorrenza" in response_text

def test_both_fine_ricorrenza(client):
    inizio = datetime.now()
    fine = inizio + timedelta(hours=1)
    termine = inizio + timedelta(days=5)
    invalid_data = {
        "tipo": TipoEvento.ESAME.name,
        "tipoSlot": TipoSlot.SINGOLO.name,
        "inizio": inizio.strftime("%Y-%m-%d %H:%M:%S"),
        "fine": fine.strftime("%Y-%m-%d %H:%M:%S"),  
        "frequenza": Frequenze.GIORNALIERA.name,
        "count": 5,
        "until": termine.strftime("%Y-%m-%d %H:%M:%S")  #entrambe opzioni per termine specificate
    }
    response = client.post('/admin/evento/new/', data=invalid_data)
    response_text = response.data.decode('utf-8')
    assert "Specificare solo un termine per la ricorrenza" in response_text

def test_invalid_until(client):
    inizio = datetime.now()
    fine = inizio + timedelta(hours=1)
    termine = inizio - timedelta(days=5)
    invalid_data = {
        "tipo": TipoEvento.ESAME.name,
        "tipoSlot": TipoSlot.SINGOLO.name,
        "inizio": inizio.strftime("%Y-%m-%d %H:%M:%S"),
        "fine": fine.strftime("%Y-%m-%d %H:%M:%S"), 
        "frequenza": Frequenze.GIORNALIERA.name,
        "count": None,
        "until": termine.strftime("%Y-%m-%d %H:%M:%S")  #fine ricorrenza prima di inizio 
    }
    response = client.post('/admin/evento/new/', data=invalid_data)
    response_text = response.data.decode('utf-8')
    assert "Data termine ricorrenza non valida" in response_text


def test_invalid_count(client):
    inizio = datetime.now()
    fine = inizio + timedelta(hours=1)
    invalid_data = {
        "tipo": TipoEvento.ESAME.name,
        "tipoSlot": TipoSlot.SINGOLO.name,
        "inizio": inizio.strftime("%Y-%m-%d %H:%M:%S"),
        "fine": fine.strftime("%Y-%m-%d %H:%M:%S"),  
        "frequenza": Frequenze.GIORNALIERA.name,
        "count": -2,    #Count negativo
        "until": None
    }
    response = client.post('/admin/evento/new/', data=invalid_data)
    response_text = response.data.decode('utf-8')
    assert "Numero di ricorrenze deve essere maggiore di 0" in response_text

def test_fine_before_inizio_ricorrenza(client):
    inizio = datetime.now()
    fine = inizio - timedelta(hours=1)
    invalid_data = {
        "tipo": TipoEvento.ESAME.name,
        "tipoSlot": TipoSlot.SINGOLO.name,
        "inizio": inizio.strftime("%Y-%m-%d %H:%M:%S"),
        "fine": fine.strftime("%Y-%m-%d %H:%M:%S"),  # Fine prima di inizio
    }
    response = client.post('/admin/ricorrenza/new/', data=invalid_data)
    response_text = response.data.decode('utf-8')
    assert "La data di fine deve essere successiva a quella di inizio" in response_text