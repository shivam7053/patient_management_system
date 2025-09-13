# tests/test_patients.py
import pytest
from flask_jwt_extended import create_access_token
from app.models import Patient

def auth_header(app):
    with app.app_context():
        token = create_access_token(identity="testuser")
    return {"Authorization": f"Bearer {token}"}


def test_add_patient(client, app):
    headers = auth_header(app)
    payload = {
        "name": "John Doe",
        "age": 30,
        "gender": "Male",
        "diagnosis": "Kidney Stone",
        "is_admitted": True
    }

    response = client.post("/patients/", json=payload, headers=headers)

    # ✅ Check status
    assert response.status_code == 201

    # ✅ Check returned JSON
    data = response.get_json()
    assert "id" in data
    assert isinstance(data["id"], int)
    assert data["message"] == "Patient added successfully"



def test_get_all_patients(client, app):
    headers = auth_header(app)

    # First, add a patient
    client.post("/patients/", json={"name": "Jane Doe", "age": 25, "gender": "Female"}, headers=headers)

    # Now get patients
    response = client.get("/patients/", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_update_patient(client, app):
    headers = auth_header(app)

    # Create patient
    res = client.post("/patients/", json={"name": "Temp", "age": 40, "gender": "Male"}, headers=headers)
    pid = res.get_json()["id"]

    # Update patient
    response = client.put(f"/patients/{pid}", json={"diagnosis": "Updated Diagnosis"}, headers=headers)
    assert response.status_code == 200
    assert response.get_json()["message"] == "Patient updated successfully"


def test_delete_patient(client, app):
    headers = auth_header(app)

    # Create patient
    res = client.post("/patients/", json={"name": "DeleteMe", "age": 50, "gender": "Female"}, headers=headers)
    pid = res.get_json()["id"]

    # Delete patient
    response = client.delete(f"/patients/{pid}", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["message"] == "Patient deleted successfully"
