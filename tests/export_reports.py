import pytest
from app import create_app, db
from app.models import User, Patient, Appointment, Doctor, Bill, Payment, Bed
from flask_jwt_extended import create_access_token
from datetime import datetime

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        # create user
        user = User(username="testuser", role="staff")
        user.set_password("pass")
        db.session.add(user)
        # create doctor
        doctor = Doctor(name="Dr. Smith", specialization="Cardiology")
        db.session.add(doctor)
        # create patients
        for i in range(2):
            p = Patient(name=f"Patient{i+1}", age=30+i, gender="Male")
            db.session.add(p)
        # create bed
        bed = Bed(bed_number="B01", status="available")
        db.session.add(bed)
        # create bill
        bill = Bill(patient_id=1, total_amount=100, status="pending")
        db.session.add(bill)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def headers(app):
    with app.app_context():
        user = User.query.first()
        token = create_access_token(identity={"id": user.id, "role": user.role})
        return {"Authorization": f"Bearer {token}"}

# ------------------ Export Tests ------------------

def test_export_patients_csv(client, headers):
    response = client.get("/export/patients?format=csv", headers=headers)
    assert response.status_code == 200
    assert response.headers['Content-Disposition'].endswith(".csv\"")

def test_export_patients_excel(client, headers):
    response = client.get("/export/patients?format=excel", headers=headers)
    assert response.status_code == 200
    assert response.headers['Content-Disposition'].endswith(".xlsx\"")

def test_export_bills_csv(client, headers):
    response = client.get("/export/bills?format=csv", headers=headers)
    assert response.status_code == 200
    assert response.headers['Content-Disposition'].endswith(".csv\"")

def test_export_bills_excel(client, headers):
    response = client.get("/export/bills?format=excel", headers=headers)
    assert response.status_code == 200
    assert response.headers['Content-Disposition'].endswith(".xlsx\"")

def test_export_beds_csv(client, headers):
    response = client.get("/export/beds?format=csv", headers=headers)
    assert response.status_code == 200
    assert response.headers['Content-Disposition'].endswith(".csv\"")

def test_export_beds_excel(client, headers):
    response = client.get("/export/beds?format=excel", headers=headers)
    assert response.status_code == 200
    assert response.headers['Content-Disposition'].endswith(".xlsx\"")

def test_export_no_records(client, headers):
    # Delete all patients
    with client.application.app_context():
        from app.models import Patient
        Patient.query.delete()
        db.session.commit()
    response = client.get("/export/patients?format=csv", headers=headers)
    assert response.status_code == 404
    assert response.get_json()["message"] == "No records found"
