import pytest
from app import create_app, db
from app.models import User, Patient, Appointment
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
        token = create_access_token(identity={"id": user.id, "role": user.role})
        return token

@pytest.fixture
def headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def patient(client, headers):
    # Create a patient for appointment
    resp = client.post("/patients/", json={"name": "John Doe", "age": 30, "gender": "male"}, headers=headers)
    return resp.get_json()["id"]

# ----------------- Appointments Tests -----------------

def test_add_appointment(client, headers, patient):
    payload = {
        "patient_id": patient,
        "doctor_name": "Dr. Smith",
        "date": "2025-09-12 10:00:00"
    }
    response = client.post("/appointments/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data
    assert data["message"] == "Appointment created successfully"

def test_get_all_appointments(client, headers, patient):
    client.post("/appointments/", json={"patient_id": patient, "doctor_name": "Dr. Smith", "date": "2025-09-12 10:00:00"}, headers=headers)
    response = client.get("/appointments/", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_get_single_appointment(client, headers, patient):
    resp = client.post("/appointments/", json={"patient_id": patient, "doctor_name": "Dr. Smith", "date": "2025-09-12 10:00:00"}, headers=headers)
    appointment_id = resp.get_json()["id"]

    response = client.get(f"/appointments/{appointment_id}", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == appointment_id
    assert data["doctor_name"] == "Dr. Smith"

def test_update_appointment(client, headers, patient):
    resp = client.post("/appointments/", json={"patient_id": patient, "doctor_name": "Dr. Smith", "date": "2025-09-12 10:00:00"}, headers=headers)
    appointment_id = resp.get_json()["id"]

    update_data = {"doctor_name": "Dr. John", "status": "Completed"}
    response = client.put(f"/appointments/{appointment_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Appointment updated successfully"

def test_delete_appointment(client, headers, patient):
    resp = client.post("/appointments/", json={"patient_id": patient, "doctor_name": "Dr. Smith", "date": "2025-09-12 10:00:00"}, headers=headers)
    appointment_id = resp.get_json()["id"]

    response = client.delete(f"/appointments/{appointment_id}", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Appointment deleted successfully"
