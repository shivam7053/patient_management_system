from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Bed, Patient
from flask_jwt_extended import jwt_required
from datetime import datetime

beds_bp = Blueprint("beds", __name__)

# Initialize beds (run once at setup)
@beds_bp.route("/init", methods=["POST"])
@jwt_required()
def init_beds():
    existing = Bed.query.count()
    if existing > 0:
        return jsonify({"message": "Beds already initialized"}), 400
    for i in range(1, 31):  # 30 beds
        b = Bed(bed_number=f"B{i:02}", status="available")
        db.session.add(b)
    db.session.commit()
    return jsonify({"message": "30 beds initialized"}), 201


# Get all beds
@beds_bp.route("/", methods=["GET"])
@jwt_required()
def get_beds():
    beds = Bed.query.all()
    result = [{
        "id": b.id,
        "bed_number": b.bed_number,
        "status": b.status,
        "patient_id": b.patient_id,
        "assigned_at": b.assigned_at.strftime("%Y-%m-%d %H:%M:%S") if b.assigned_at else None
    } for b in beds]
    return jsonify(result), 200


# Assign a bed
@beds_bp.route("/assign", methods=["POST"])
@jwt_required()
def assign_bed():
    data = request.get_json()
    patient_id = data.get("patient_id")
    bed_id = data.get("bed_id")

    bed = Bed.query.get(bed_id)
    if not bed:
        return jsonify({"error": "Bed not found"}), 404
    if bed.status != "available":
        return jsonify({"error": "Bed not available"}), 400

    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    bed.status = "occupied"
    bed.patient_id = patient_id
    bed.assigned_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": f"Bed {bed.bed_number} assigned to patient {patient.name}"}), 200


# Release a bed
@beds_bp.route("/release", methods=["POST"])
@jwt_required()
def release_bed():
    data = request.get_json()
    bed_id = data.get("bed_id")

    bed = Bed.query.get(bed_id)
    if not bed:
        return jsonify({"error": "Bed not found"}), 404
    if bed.status != "occupied":
        return jsonify({"error": "Bed is not occupied"}), 400

    bed.status = "available"
    bed.patient_id = None
    bed.assigned_at = None
    db.session.commit()

    return jsonify({"message": f"Bed {bed.bed_number} released"}), 200


# Bed stats (for visualization)
@beds_bp.route("/stats", methods=["GET"])
@jwt_required()
def bed_stats():
    total = Bed.query.count()
    available = Bed.query.filter_by(status="available").count()
    occupied = Bed.query.filter_by(status="occupied").count()
    maintenance = Bed.query.filter_by(status="maintenance").count()

    return jsonify({
        "total_beds": total,
        "available": available,
        "occupied": occupied,
        "maintenance": maintenance,
        "occupancy_rate": round((occupied / total) * 100, 2) if total else 0
    }), 200
