import pytest
from app import app as APP
from app import session
from app import serializer, ADMIN_MAIL, ADMIN_USR, ADMIN_PWD
from models import db, Studente

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

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"SRM" in response.data
    assert b"Messaggio" not in response.data

def test_index_route_error(client):
    error_message = "Messaggio di errore allert"
    response = client.get('/?error=' + error_message)
    assert response.status_code == 200
    assert b"SRM" in response.data
    assert b"Messaggio di errore allert" in response.data

def test_admin_token(client):
    token = serializer.dumps(ADMIN_MAIL, salt="ADMIN-accesso-confermato")
    response = response = client.get("/admin_login/" + token)
    assert response.status_code == 200

    decoded_email = serializer.loads(token, salt="ADMIN-accesso-confermato")
    assert decoded_email == ADMIN_MAIL

def test_admin_login_incorrect_token(client):
    token = "invalid_token"
    response = client.get('/admin_login/' + token)
    
    assert response.status_code == 200
    assert b"Token di accesso non valido" in response.data

def test_credenziali_admin(client):
    token = serializer.dumps(ADMIN_MAIL, salt="ADMIN-accesso-confermato")
    data = {
        "username": ADMIN_USR,
        "password": ADMIN_PWD,
        "rememberMe": "on"
    }
    response = client.post('/admin_login/' + token, data=data, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Home - SRM" in response.data

def test_credenziali_admin_sbagliate(client):
    token = serializer.dumps(ADMIN_MAIL, salt="ADMIN-accesso-confermato")
    data = {
        "username": "usr sbagliato",
        "password": "pwd sbagliata",
        "rememberMe": "on"
    }
    response = client.post('/admin_login/' + token, data=data, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Credenziali non valide" in response.data

def test_login_new_student(client):
    token = serializer.dumps("dsa@prova.com", salt="email-accesso-confermata")

    response = client.get("/login/" + token)

    assert response.status_code == 200
    assert b"Token di accesso scaduto o non valido" not in response.data
    assert b"Accedi" in response.data
    