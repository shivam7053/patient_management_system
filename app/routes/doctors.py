from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Doctor
from flask_jwt_extended import jwt_required

doctors_bp = Blueprint("doctors", __name__)

# ✅ Add Doctor
@doctors_bp.route("/", methods=["POST"])
@jwt_required()
def add_doctor():
    data = request.get_json()
    if not data.get("name") or not data.get("specialization"):
        return jsonify({"error": "Name and specialization required"}), 400

    doctor = Doctor(
        name=data["name"],
        specialization=data["specialization"],
        phone=data.get("phone"),
        email=data.get("email")
    )

    db.session.add(doctor)
    db.session.commit()
    return jsonify({"message": "Doctor added successfully", "id": doctor.id}), 201


# ✅ Get All Doctors
@doctors_bp.route("/", methods=["GET"])
@jwt_required()
def get_doctors():
    doctors = Doctor.query.all()
    results = [
        {
            "id": d.id,
            "name": d.name,
            "specialization": d.specialization,
            "phone": d.phone,
            "email": d.email
        }
        for d in doctors
    ]
    return jsonify(results), 200


# ✅ Get Single Doctor
@doctors_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    return jsonify({
        "id": doctor.id,
        "name": doctor.name,
        "specialization": doctor.specialization,
        "phone": doctor.phone,
        "email": doctor.email
    })


# ✅ Update Doctor
@doctors_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
def update_doctor(id):
    data = request.get_json()
    doctor = Doctor.query.get_or_404(id)

    doctor.name = data.get("name", doctor.name)
    doctor.specialization = data.get("specialization", doctor.specialization)
    doctor.phone = data.get("phone", doctor.phone)
    doctor.email = data.get("email", doctor.email)

    db.session.commit()
    return jsonify({"message": "Doctor updated successfully"})


# ✅ Delete Doctor
@doctors_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    db.session.delete(doctor)
    db.session.commit()
    return jsonify({"message": "Doctor deleted successfully"})
