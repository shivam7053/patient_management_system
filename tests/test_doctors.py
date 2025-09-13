import pytest
from app.extensions import db
from app.models import Doctor

# ------------------------------
# Fixture: Add one doctor easily
# ------------------------------
@pytest.fixture
def sample_doctor(app):
    doctor = Doctor(
        name="Dr. Test",
        specialization="Cardiology",
        phone="1234567890",
        email="drtest@example.com"
    )
    with app.app_context():
        db.session.add(doctor)
        db.session.commit()
        yield doctor
        db.session.delete(doctor)
        db.session.commit()


# ------------------------------
# Tests
# ------------------------------

def test_add_doctor(client, auth_headers):
    res = client.post("/doctors/", json={
        "name": "Dr. House",
        "specialization": "Nephrology",
        "phone": "9876543210",
        "email": "house@example.com"
    }, headers=auth_headers)

    assert res.status_code == 201
    assert res.json["message"] == "Doctor added successfully"
    assert "id" in res.json


def test_get_all_doctors(client, auth_headers, sample_doctor):
    res = client.get("/doctors/", headers=auth_headers)

    assert res.status_code == 200
    assert isinstance(res.json, list)
    assert any(d["name"] == "Dr. Test" for d in res.json)


def test_get_single_doctor(client, auth_headers, sample_doctor):
    res = client.get(f"/doctors/{sample_doctor.id}", headers=auth_headers)

    assert res.status_code == 200
    assert res.json["name"] == "Dr. Test"
    assert res.json["specialization"] == "Cardiology"


def test_update_doctor(client, auth_headers, sample_doctor):
    res = client.put(f"/doctors/{sample_doctor.id}", json={
        "specialization": "Neurology"
    }, headers=auth_headers)

    assert res.status_code == 200
    assert res.json["message"] == "Doctor updated successfully"

    # verify update
    res2 = client.get(f"/doctors/{sample_doctor.id}", headers=auth_headers)
    assert res2.json["specialization"] == "Neurology"


def test_delete_doctor(client, auth_headers, sample_doctor):
    res = client.delete(f"/doctors/{sample_doctor.id}", headers=auth_headers)

    assert res.status_code == 200
    assert res.json["message"] == "Doctor deleted successfully"

    # verify deletion
    res2 = client.get(f"/doctors/{sample_doctor.id}", headers=auth_headers)
    assert res2.status_code == 404
