from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Patient
from flask_jwt_extended import jwt_required

patients_bp = Blueprint("patients", __name__)

# ✅ Create Patient
@patients_bp.route("/", methods=["POST"])
@jwt_required()
def add_patient():
    data = request.get_json()
    if not data.get("name") or not data.get("age") or not data.get("gender"):
        return jsonify({"error": "Name, age and gender required"}), 400

    patient = Patient(
        name=data["name"],
        age=data["age"],
        gender=data["gender"],
        diagnosis=data.get("diagnosis", ""),
        is_admitted=data.get("is_admitted", False)
    )

    db.session.add(patient)
    db.session.commit()

    return jsonify({"message": "Patient added successfully", "id": patient.id}), 201


# ✅ Get All Patients
@patients_bp.route("/", methods=["GET"])
@jwt_required()
def get_patients():
    patients = Patient.query.all()
    results = [
        {
            "id": p.id,
            "name": p.name,
            "age": p.age,
            "gender": p.gender,
            "diagnosis": p.diagnosis,
            "is_admitted": p.is_admitted,
            "admitted_on": p.admitted_on.strftime("%Y-%m-%d %H:%M:%S")
        }
        for p in patients
    ]
    return jsonify(results), 200


# ✅ Get Single Patient
@patients_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_patient(id):
    patient = Patient.query.get_or_404(id)
    return jsonify({
        "id": patient.id,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "diagnosis": patient.diagnosis,
        "is_admitted": patient.is_admitted,
        "admitted_on": patient.admitted_on.strftime("%Y-%m-%d %H:%M:%S")
    })


# ✅ Update Patient
@patients_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
def update_patient(id):
    data = request.get_json()
    patient = Patient.query.get_or_404(id)

    patient.name = data.get("name", patient.name)
    patient.age = data.get("age", patient.age)
    patient.gender = data.get("gender", patient.gender)
    patient.diagnosis = data.get("diagnosis", patient.diagnosis)
    patient.is_admitted = data.get("is_admitted", patient.is_admitted)

    db.session.commit()
    return jsonify({"message": "Patient updated successfully"})


# ✅ Delete Patient
@patients_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_patient(id):
    patient = Patient.query.get_or_404(id)
    db.session.delete(patient)
    db.session.commit()
    return jsonify({"message": "Patient deleted successfully"})
