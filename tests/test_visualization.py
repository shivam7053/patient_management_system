import pytest
from app import create_app, db
from app.models import User, Patient, Appointment, Doctor, Bill, Payment, Bed
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        # Create user
        user = User(username="testuser", role="staff")
        user.set_password("pass")
        db.session.add(user)
        # Create doctor
        doctor = Doctor(name="Dr. Smith", specialization="Cardiology")
        db.session.add(doctor)
        # Create patients
        for i in range(3):
            p = Patient(name=f"Patient{i+1}", age=30+i, gender="Male")
            db.session.add(p)
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

# ---------------- Visualization Tests -----------------

def test_daily_patients(client, headers):
    response = client.get("/visualization/patients/daily?days=3", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 3
    assert "patients" in data[0]

def test_appointment_status(client, headers):
    # Add appointments
    with client.application.app_context():
        patient = Patient.query.first()
        doctor = Doctor.query.first()
        for status in ["scheduled", "completed", "cancelled"]:
            appt = Appointment(patient_id=patient.id, doctor_name=doctor.name, status=status)
            db.session.add(appt)
        db.session.commit()

    response = client.get("/visualization/appointments/status", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == 3
    assert data["completed"] == 1
    assert data["scheduled"] == 1
    assert data["cancelled"] == 1

def test_doctor_workload(client, headers):
    with client.application.app_context():
        patient = Patient.query.first()
        doctor = Doctor.query.first()
        appt = Appointment(patient_id=patient.id, doctor_name=doctor.name)
        db.session.add(appt)
        db.session.commit()

    response = client.get("/visualization/doctor/workload", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data[0]["appointments"] >= 1

def test_revenue_daily(client, headers):
    with client.application.app_context():
        patient = Patient.query.first()
        bill = Bill(patient_id=patient.id, total_amount=100)
        db.session.add(bill)
        db.session.flush()
        payment = Payment(bill_id=bill.id, amount=100, method="cash")
        db.session.add(payment)
        db.session.commit()

    response = client.get("/visualization/revenue/daily?days=1", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data[0]["revenue"] == 100

def test_patients_aggregate(client, headers):
    response = client.get("/visualization/patients/aggregate?period=daily", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_revenue_aggregate(client, headers):
    response = client.get("/visualization/revenue/aggregate?period=daily", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_bed_occupancy_aggregate(client, headers):
    with client.application.app_context():
        # create 5 beds
        for i in range(5):
            bed = Bed(bed_number=f"B{i+1}", status="occupied", assigned_at=datetime.utcnow())
            db.session.add(bed)
        db.session.commit()

    response = client.get("/visualization/beds/occupancy/aggregate?period=daily", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 7
    assert "occupancy_rate" in data[0]
