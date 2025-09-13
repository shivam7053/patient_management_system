import pytest
from app.extensions import db
from app.models import Patient, Bill, Payment


@pytest.fixture
def sample_patient(app):
    """Create one patient to attach bills."""
    patient = Patient(name="Billing Test", age=40, gender="Male")
    with app.app_context():
        db.session.add(patient)
        db.session.commit()
        yield patient
        db.session.delete(patient)
        db.session.commit()


def test_create_bill(client, auth_headers, sample_patient):
    res = client.post("/billing/", json={
        "patient_id": sample_patient.id,
        "items": [
            {"description": "Consultation", "quantity": 1, "unit_price": 500},
            {"description": "Blood Test", "quantity": 2, "unit_price": 300}
        ]
    }, headers=auth_headers)

    assert res.status_code == 201
    data = res.json
    assert data["message"] == "Bill created"
    assert "bill_id" in data


def test_get_bills_for_patient(client, auth_headers, sample_patient):
    # create one bill first
    client.post("/billing/", json={
        "patient_id": sample_patient.id,
        "items": [{"description": "X-Ray", "quantity": 1, "unit_price": 1000}]
    }, headers=auth_headers)

    res = client.get(f"/billing/patient/{sample_patient.id}", headers=auth_headers)
    assert res.status_code == 200
    bills = res.json
    assert isinstance(bills, list)
    assert bills[0]["total_amount"] == 1000


def test_get_single_bill(client, auth_headers, sample_patient):
    bill_res = client.post("/billing/", json={
        "patient_id": sample_patient.id,
        "items": [{"description": "MRI", "quantity": 1, "unit_price": 2000}]
    }, headers=auth_headers)
    bill_id = bill_res.json["bill_id"]

    res = client.get(f"/billing/{bill_id}", headers=auth_headers)
    assert res.status_code == 200
    bill = res.json
    assert bill["total_amount"] == 2000
    assert bill["items"][0]["description"] == "MRI"


def test_pay_bill_and_status_update(client, auth_headers, sample_patient):
    bill_res = client.post("/billing/", json={
        "patient_id": sample_patient.id,
        "items": [{"description": "Ultrasound", "quantity": 1, "unit_price": 1500}]
    }, headers=auth_headers)
    bill_id = bill_res.json["bill_id"]

    res = client.post(f"/billing/{bill_id}/pay", json={
        "amount": 1500,
        "method": "cash",
        "reference": "TXN123"
    }, headers=auth_headers)

    assert res.status_code == 201
    pay_data = res.json
    assert pay_data["message"] == "Payment recorded"
    assert pay_data["bill_status"] == "paid"


def test_update_bill_add_notes(client, auth_headers, sample_patient):
    bill_res = client.post("/billing/", json={
        "patient_id": sample_patient.id,
        "items": [{"description": "ECG", "quantity": 1, "unit_price": 400}]
    }, headers=auth_headers)
    bill_id = bill_res.json["bill_id"]

    res = client.put(f"/billing/{bill_id}", json={"notes": "urgent case"}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json["message"] == "Bill updated"

    # verify notes updated
    res2 = client.get(f"/billing/{bill_id}", headers=auth_headers)
    assert res2.json["notes"] == "urgent case"


def test_revenue_report(client, auth_headers, sample_patient):
    bill_res = client.post("/billing/", json={
        "patient_id": sample_patient.id,
        "items": [{"description": "CT Scan", "quantity": 1, "unit_price": 3000}]
    }, headers=auth_headers)
    bill_id = bill_res.json["bill_id"]

    client.post(f"/billing/{bill_id}/pay", json={"amount": 3000, "method": "upi"}, headers=auth_headers)

    res = client.get("/billing/reports/revenue/daily", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json, list)
    assert any(r["total_paid"] >= 3000 for r in res.json)


def test_outstanding_report(client, auth_headers, sample_patient):
    # create bill with partial payment
    bill_res = client.post("/billing/", json={
        "patient_id": sample_patient.id,
        "items": [{"description": "Surgery", "quantity": 1, "unit_price": 10000}]
    }, headers=auth_headers)
    bill_id = bill_res.json["bill_id"]

    client.post(f"/billing/{bill_id}/pay", json={"amount": 5000, "method": "card"}, headers=auth_headers)

    res = client.get("/billing/reports/outstanding", headers=auth_headers)
    assert res.status_code == 200
    data = res.json
    assert isinstance(data, list)
    assert data[0]["outstanding"] == 5000
