import pytest
from app import create_app, db
from app.models import User
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

# ----------------- Auth Tests -----------------

def test_register_user(client):
    payload = {"username": "testuser", "password": "password123", "role": "staff"}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "User registered successfully"

def test_register_duplicate_user(client):
    payload = {"username": "duplicate", "password": "pass"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "User already exists"

def test_login_user_success(client):
    client.post("/auth/register", json={"username": "loginuser", "password": "pass"})
    response = client.post("/auth/login", json={"username": "loginuser", "password": "pass"})
    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data

def test_login_user_fail(client):
    response = client.post("/auth/login", json={"username": "nouser", "password": "wrong"})
    assert response.status_code == 401
    data = response.get_json()
    assert data["error"] == "Invalid credentials"

def test_protected_route(client, app):
    # create user and generate access token
    with app.app_context():
        user = User(username="protected", role="staff")
        user.set_password("pass")
        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity={"id": user.id, "role": user.role})

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/profile", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["user"]["id"] == user.id
