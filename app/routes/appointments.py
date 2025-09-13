from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Appointment, Patient
from flask_jwt_extended import jwt_required
from datetime import datetime

appointments_bp = Blueprint("appointments", __name__)

# ✅ Create Appointment
@appointments_bp.route("/", methods=["POST"])
@jwt_required()
def add_appointment():
    data = request.get_json()
    if not data.get("patient_id") or not data.get("doctor_name") or not data.get("date"):
        return jsonify({"error": "Patient ID, doctor name and date required"}), 400

    patient = Patient.query.get(data["patient_id"])
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    appointment = Appointment(
        patient_id=data["patient_id"],
        doctor_name=data["doctor_name"],
        date=datetime.strptime(data["date"], "%Y-%m-%d %H:%M:%S"),
        status=data.get("status", "Scheduled")
    )

    db.session.add(appointment)
    db.session.commit()
    return jsonify({"message": "Appointment created successfully", "id": appointment.id}), 201


# ✅ Get All Appointments
@appointments_bp.route("/", methods=["GET"])
@jwt_required()
def get_appointments():
    appointments = Appointment.query.all()
    results = [
        {
            "id": a.id,
            "patient_id": a.patient_id,
            "patient_name": a.patient.name,
            "doctor_name": a.doctor_name,
            "date": a.date.strftime("%Y-%m-%d %H:%M:%S"),
            "status": a.status
        }
        for a in appointments
    ]
    return jsonify(results), 200


# ✅ Get Single Appointment
@appointments_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    return jsonify({
        "id": appointment.id,
        "patient_id": appointment.patient_id,
        "patient_name": appointment.patient.name,
        "doctor_name": appointment.doctor_name,
        "date": appointment.date.strftime("%Y-%m-%d %H:%M:%S"),
        "status": appointment.status
    })


# ✅ Update Appointment
@appointments_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
def update_appointment(id):
    data = request.get_json()
    appointment = Appointment.query.get_or_404(id)

    if data.get("doctor_name"):
        appointment.doctor_name = data["doctor_name"]
    if data.get("date"):
        appointment.date = datetime.strptime(data["date"], "%Y-%m-%d %H:%M:%S")
    if data.get("status"):
        appointment.status = data["status"]

    db.session.commit()
    return jsonify({"message": "Appointment updated successfully"})


# ✅ Delete Appointment
@appointments_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    db.session.delete(appointment)
    db.session.commit()
    return jsonify({"message": "Appointment deleted successfully"})
