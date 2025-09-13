import csv
import io
import pandas as pd
from flask import Blueprint, send_file, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import Patient, Appointment, Bill, Bed

export_bp = Blueprint("export", __name__)

# ------------------ Export Patients ------------------
@export_bp.route("/patients", methods=["GET"])
@jwt_required()
def export_patients():
    patient_type = request.args.get("patient_type")
    doctor_name = request.args.get("doctor_name")  # changed from doctor_id
    format_ = request.args.get("format", "csv")  # csv or excel

    query = Patient.query
    if patient_type:
        query = query.filter_by(type=patient_type)
    if doctor_name:
        query = query.join(Patient.appointments).filter(Appointment.doctor_name == doctor_name)

    patients = query.all()
    data = [{
        "Patient ID": p.id,
        "Name": p.name,
        "Age": p.age,
        "Gender": p.gender,
        "Type": p.type,
        "Admitted On": p.admitted_on.strftime("%Y-%m-%d %H:%M:%S")
    } for p in patients]

    if not data:
        return jsonify({"message": "No records found"}), 404

    return send_file_data(data, "patients", format_)


# ------------------ Export Bills ------------------
@export_bp.route("/bills", methods=["GET"])
@jwt_required()
def export_bills():
    patient_id = request.args.get("patient_id")
    format_ = request.args.get("format", "csv")

    query = Bill.query
    if patient_id:
        query = query.filter_by(patient_id=int(patient_id))
    bills = query.all()

    data = []
    for b in bills:
        paid = sum([p.amount for p in b.payments]) if b.payments else 0.0
        due = round(b.total_amount - paid, 2)
        data.append({
            "Bill ID": b.id, 
            "Patient": b.patient.name,
            "Total Amount": b.total_amount,
            "Paid Amount": paid,
            "Due Amount": due,
            "Status": b.status,
            "Created At": b.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    if not data:
        return jsonify({"message": "No records found"}), 404

    return send_file_data(data, "bills", format_)


# ------------------ Export Beds ------------------
@export_bp.route("/beds", methods=["GET"])
@jwt_required()
def export_beds():
    format_ = request.args.get("format", "csv")
    beds = Bed.query.all()

    data = []
    for b in beds:
        data.append({
            "Bed Number": b.bed_number,
            "Status": b.status,
            "Patient": b.patient.name if b.patient else "",
            "Assigned At": b.assigned_at.strftime("%Y-%m-%d %H:%M:%S") if b.assigned_at else ""
        })

    if not data:
        return jsonify({"message": "No records found"}), 404

    return send_file_data(data, "beds", format_)


# ------------------ Helper Function ------------------
def send_file_data(data, filename, format_):
    """Send data as CSV or Excel file"""
    if format_ == "excel":
        df = pd.DataFrame(data)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        return send_file(output, download_name=f"{filename}.xlsx", as_attachment=True)
    else:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()), download_name=f"{filename}.csv", as_attachment=True)
