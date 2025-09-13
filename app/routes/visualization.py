from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.models import Patient, Appointment, Doctor, Bill, Bed
from app.extensions import db
from sqlalchemy import func
from datetime import datetime, timedelta

viz_bp = Blueprint("visualization", __name__)

# ✅ Daily patients for last N days
@viz_bp.route("/patients/daily", methods=["GET"])
@jwt_required()
def daily_patients():
    days = int(request.args.get("days", 7))
    patient_type = request.args.get("patient_type")  # optional
    doctor_name = request.args.get("doctor_name")  # optional

    today = datetime.utcnow().date()
    result = []

    for i in range(days):
        day = today - timedelta(days=i)
        query = Patient.query.filter(func.date(Patient.admitted_on) == day)
        if patient_type:
            query = query.filter_by(type=patient_type)
        if doctor_name:
            query = query.join(Patient.appointments).filter(Appointment.doctor_name == doctor_name)

        count = query.distinct().count()
        result.append({"date": day.strftime("%Y-%m-%d"), "patients": count})

    return jsonify(result[::-1])


# ✅ Completed vs scheduled vs cancelled appointments
@viz_bp.route("/appointments/status", methods=["GET"])
@jwt_required()
def appointment_status():
    total = Appointment.query.count()
    completed = Appointment.query.filter_by(status="Completed").count()
    scheduled = Appointment.query.filter_by(status="Scheduled").count()
    cancelled = Appointment.query.filter_by(status="Cancelled").count()
    return jsonify({
        "total": total,
        "completed": completed,
        "scheduled": scheduled,
        "cancelled": cancelled
    })


# ✅ Doctor workload (appointments per doctor, by name)
@viz_bp.route("/doctor/workload", methods=["GET"])
@jwt_required()
def doctor_workload():
    doctors = Doctor.query.all()
    result = []
    for d in doctors:
        count = Appointment.query.filter_by(doctor_name=d.name).count()
        result.append({
            "doctor_id": d.id,
            "doctor_name": d.name,
            "specialization": d.specialization,
            "appointments": count
        })
    return jsonify(result)


# ✅ Daily revenue for last N days
@viz_bp.route("/revenue/daily", methods=["GET"])
@jwt_required()
def revenue_daily():
    days = int(request.args.get("days", 7))
    today = datetime.utcnow().date()
    result = []
    for i in range(days):
        day = today - timedelta(days=i)
        total = db.session.query(func.sum(Bill.total_amount)) \
            .filter(func.date(Bill.created_at) == day).scalar() or 0
        result.append({"date": day.strftime("%Y-%m-%d"), "revenue": total})
    return jsonify(result[::-1])


# ✅ Patients aggregate (daily / weekly / monthly)
@viz_bp.route("/patients/aggregate", methods=["GET"])
@jwt_required()
def aggregate_patients():
    period = request.args.get("period", "daily")
    patient_type = request.args.get("patient_type")
    doctor_name = request.args.get("doctor_name")

    query = Patient.query
    if patient_type:
        query = query.filter_by(type=patient_type)
    if doctor_name:
        query = query.join(Patient.appointments).filter(Appointment.doctor_name == doctor_name)

    today = datetime.utcnow().date()
    result = []

    if period == "daily":
        for i in range(7):
            day = today - timedelta(days=i)
            count = query.filter(func.date(Patient.admitted_on) == day).distinct().count()
            result.append({"date": day.strftime("%Y-%m-%d"), "patients": count})

    elif period == "weekly":
        for i in range(4):
            start = today - timedelta(days=today.weekday()) - timedelta(weeks=i)
            end = start + timedelta(days=6)
            count = query.filter(func.date(Patient.admitted_on) >= start,
                                 func.date(Patient.admitted_on) <= end).distinct().count()
            result.append({
                "week_start": start.strftime("%Y-%m-%d"),
                "week_end": end.strftime("%Y-%m-%d"),
                "patients": count
            })

    elif period == "monthly":
        for i in range(6):
            month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            count = query.filter(func.date(Patient.admitted_on) >= month_start,
                                 func.date(Patient.admitted_on) < next_month).distinct().count()
            result.append({
                "month": month_start.strftime("%Y-%m"),
                "patients": count
            })

    return jsonify(result[::-1])


# ✅ Revenue aggregate (daily / weekly / monthly)
@viz_bp.route("/revenue/aggregate", methods=["GET"])
@jwt_required()
def revenue_aggregate():
    period = request.args.get("period", "daily")
    today = datetime.utcnow().date()
    result = []

    if period == "daily":
        for i in range(7):
            day = today - timedelta(days=i)
            total = db.session.query(func.sum(Bill.total_amount)) \
                .filter(func.date(Bill.created_at) == day).scalar() or 0
            result.append({"date": day.strftime("%Y-%m-%d"), "revenue": total})

    elif period == "weekly":
        for i in range(4):
            start = today - timedelta(days=today.weekday()) - timedelta(weeks=i)
            end = start + timedelta(days=6)
            total = db.session.query(func.sum(Bill.total_amount)) \
                .filter(func.date(Bill.created_at) >= start,
                        func.date(Bill.created_at) <= end).scalar() or 0
            result.append({
                "week_start": start.strftime("%Y-%m-%d"),
                "week_end": end.strftime("%Y-%m-%d"),
                "revenue": total
            })

    elif period == "monthly":
        for i in range(6):
            month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            total = db.session.query(func.sum(Bill.total_amount)) \
                .filter(func.date(Bill.created_at) >= month_start,
                        func.date(Bill.created_at) < next_month).scalar() or 0
            result.append({"month": month_start.strftime("%Y-%m"), "revenue": total})

    return jsonify(result[::-1])


# ✅ Bed occupancy aggregate
@viz_bp.route("/beds/occupancy/aggregate", methods=["GET"])
@jwt_required()
def bed_occupancy_aggregate():
    period = request.args.get("period", "daily")
    today = datetime.utcnow().date()
    result = []

    if period == "daily":
        for i in range(7):
            day = today - timedelta(days=i)
            occupied = Bed.query.filter(func.date(Bed.assigned_at) == day,
                                        Bed.status == "occupied").count()
            total = Bed.query.count()
            rate = round((occupied / total) * 100, 2) if total else 0
            result.append({"date": day.strftime("%Y-%m-%d"), "occupancy_rate": rate})

    elif period == "weekly":
        for i in range(4):
            start = today - timedelta(days=today.weekday()) - timedelta(weeks=i)
            end = start + timedelta(days=6)
            occupied = Bed.query.filter(func.date(Bed.assigned_at) >= start,
                                        func.date(Bed.assigned_at) <= end,
                                        Bed.status == "occupied").count()
            total = Bed.query.count()
            rate = round((occupied / total) * 100, 2) if total else 0
            result.append({
                "week_start": start.strftime("%Y-%m-%d"),
                "week_end": end.strftime("%Y-%m-%d"),
                "occupancy_rate": rate
            })

    elif period == "monthly":
        for i in range(6):
            month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            occupied = Bed.query.filter(func.date(Bed.assigned_at) >= month_start,
                                        func.date(Bed.assigned_at) < next_month,
                                        Bed.status == "occupied").count()
            total = Bed.query.count()
            rate = round((occupied / total) * 100, 2) if total else 0
            result.append({
                "month": month_start.strftime("%Y-%m"),
                "occupancy_rate": rate
            })

    return jsonify(result[::-1])
