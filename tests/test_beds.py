import pytest
from app import create_app, db
from app.models import User, Patient, Bed
from flask_jwt_extended import create_access_token
from datetime import datetime

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        # Create a user for JWT
        user = User(username="testuser", role="staff")
        user.set_password("pass")
        db.session.add(user)
        # Add a patient
        patient = Patient(name="John Doe", age=30, gender="Male")
        db.session.add(patient)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def access_token(app):
    with app.app_context():
        user = User.query.first()
        return create_access_token(identity={"id": user.id, "role": user.role})

@pytest.fixture
def headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def patient_id(app):
    with app.app_context():
        return Patient.query.first().id

# ----------------- Beds Tests -----------------

def test_init_beds(client, headers):
    response = client.post("/beds/init", headers=headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "30 beds initialized"

def test_get_beds(client, headers):
    client.post("/beds/init", headers=headers)
    response = client.get("/beds/", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 30

def test_assign_bed(client, headers, patient_id):
    client.post("/beds/init", headers=headers)
    # assign first bed
    bed_id = 1
    payload = {"bed_id": bed_id, "patient_id": patient_id}
    response = client.post("/beds/assign", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "assigned to patient" in data["message"]

def test_release_bed(client, headers, patient_id):
    client.post("/beds/init", headers=headers)
    # assign first bed
    client.post("/beds/assign", json={"bed_id": 1, "patient_id": patient_id}, headers=headers)
    # release
    response = client.post("/beds/release", json={"bed_id": 1}, headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "released" in data["message"]

def test_bed_stats(client, headers, patient_id):
    client.post("/beds/init", headers=headers)
    # assign some beds
    client.post("/beds/assign", json={"bed_id": 1, "patient_id": patient_id}, headers=headers)
    client.post("/beds/assign", json={"bed_id": 2, "patient_id": patient_id}, headers=headers)
    response = client.get("/beds/stats", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["total_beds"] == 30
    assert data["occupied"] == 2
    assert data["available"] == 28
