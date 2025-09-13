# app/routes/billing.py
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Bill, BillItem, Payment, Patient, Appointment
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from datetime import datetime

billing_bp = Blueprint("billing", __name__)

# Helper: compute total from items list
def compute_total_from_items(items):
    total = 0.0
    for it in items:
        qty = int(it.get("quantity", 1))
        unit = float(it.get("unit_price", 0.0))
        total += qty * unit
    return total

# Create a bill with items
@billing_bp.route("/", methods=["POST"])
@jwt_required()
def create_bill():
    data = request.get_json() or {}
    patient_id = data.get("patient_id")
    if not patient_id:
        return jsonify({"error": "patient_id required"}), 400

    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "patient not found"}), 404

    appointment_id = data.get("appointment_id")
    if appointment_id:
        appt = Appointment.query.get(appointment_id)
        if not appt:
            return jsonify({"error": "appointment not found"}), 404

    items = data.get("items", [])
    if not items:
        return jsonify({"error": "At least one bill item required"}), 400

    total = compute_total_from_items(items)

    bill = Bill(
        patient_id=patient_id,
        appointment_id=appointment_id,
        total_amount=total,
        status="pending",
        currency=data.get("currency", "INR"),
        notes=data.get("notes")
    )
    db.session.add(bill)
    db.session.flush()  # get bill.id

    # add items
    for it in items:
        bi = BillItem(
            bill_id=bill.id,
            description=it.get("description", "Item"),
            quantity=int(it.get("quantity", 1)),
            unit_price=float(it.get("unit_price", 0.0))
        )
        db.session.add(bi)

    db.session.commit()
    return jsonify({"message": "Bill created", "bill_id": bill.id}), 201


# Get all bills for a patient
@billing_bp.route("/patient/<int:patient_id>", methods=["GET"])
@jwt_required()
def get_bills_for_patient(patient_id):
    bills = Bill.query.filter_by(patient_id=patient_id).order_by(Bill.created_at.desc()).all()
    result = []
    for b in bills:
        paid = sum([p.amount for p in b.payments]) if b.payments else 0.0
        result.append({
            "id": b.id,
            "created_at": b.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "total_amount": b.total_amount,
            "paid_amount": paid,
            "status": b.status,
            "currency": b.currency,
            "notes": b.notes
        })
    return jsonify(result), 200


# Get single bill with items & payments
@billing_bp.route("/<int:bill_id>", methods=["GET"])
@jwt_required()
def get_bill(bill_id):
    b = Bill.query.get_or_404(bill_id)
    items = [{
        "id": it.id,
        "description": it.description,
        "quantity": it.quantity,
        "unit_price": it.unit_price,
        "amount": it.amount
    } for it in b.items]
    payments = [{
        "id": p.id,
        "amount": p.amount,
        "method": p.method,
        "paid_at": p.paid_at.strftime("%Y-%m-%d %H:%M:%S"),
        "reference": p.reference
    } for p in b.payments]
    paid = sum(p["amount"] for p in payments) if payments else 0.0
    due = round(b.total_amount - paid, 2)
    return jsonify({
        "id": b.id,
        "patient_id": b.patient_id,
        "appointment_id": b.appointment_id,
        "created_at": b.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "total_amount": b.total_amount,
        "paid_amount": paid,
        "due_amount": due,
        "status": b.status,
        "items": items,
        "payments": payments,
        "notes": b.notes
    }), 200


# Record a payment against a bill
@billing_bp.route("/<int:bill_id>/pay", methods=["POST"])
@jwt_required()
def pay_bill(bill_id):
    data = request.get_json() or {}
    amount = float(data.get("amount", 0.0))
    method = data.get("method")
    if amount <= 0 or not method:
        return jsonify({"error": "amount and method required"}), 400

    bill = Bill.query.get_or_404(bill_id)
    payment = Payment(
        bill_id=bill.id,
        amount=amount,
        method=method,
        reference=data.get("reference")
    )
    db.session.add(payment)
    db.session.flush()

    # update bill status
    total_paid = sum([p.amount for p in bill.payments]) + amount
    if total_paid >= bill.total_amount:
        bill.status = "paid"
    elif total_paid > 0:
        bill.status = "partial"
    db.session.commit()
    return jsonify({"message": "Payment recorded", "payment_id": payment.id, "bill_status": bill.status}), 201


# Update bill (e.g., cancel, add notes) or modify items (simple version)
@billing_bp.route("/<int:bill_id>", methods=["PUT"])
@jwt_required()
def update_bill(bill_id):
    data = request.get_json() or {}
    bill = Bill.query.get_or_404(bill_id)
    # allow cancelling
    if data.get("status") in ("pending", "cancelled"):
        bill.status = data.get("status")
    if "notes" in data:
        bill.notes = data.get("notes")
    # Optionally update items: full replace
    items = data.get("items")
    if items is not None:
        # delete existing items
        BillItem.query.filter_by(bill_id=bill.id).delete()
        db.session.flush()
        for it in items:
            bi = BillItem(
                bill_id=bill.id,
                description=it.get("description", "Item"),
                quantity=int(it.get("quantity", 1)),
                unit_price=float(it.get("unit_price", 0.0))
            )
            db.session.add(bi)
        # recompute total
        bill.total_amount = compute_total_from_items(items)
    db.session.commit()
    return jsonify({"message": "Bill updated", "bill_id": bill.id}), 200


# Revenue report: daily totals for last N days (default 7)
@billing_bp.route("/reports/revenue/daily", methods=["GET"])
@jwt_required()
def revenue_daily():
    days = int(request.args.get("days", 7))
    # Group payments by date
    q = db.session.query(
        func.date(Payment.paid_at).label("date"),
        func.sum(Payment.amount).label("total_paid")
    ).group_by(func.date(Payment.paid_at)).order_by(func.date(Payment.paid_at).desc()).limit(days)
    rows = q.all()
    result = [{"date": r.date.strftime("%Y-%m-%d"), "total_paid": float(r.total_paid or 0.0)} for r in rows]
    return jsonify(result[::-1]), 200  # return oldest -> newest


# Outstanding bills (unpaid amount per patient)
@billing_bp.route("/reports/outstanding", methods=["GET"])
@jwt_required()
def outstanding_report():
    # compute outstanding per bill then group by patient
    bills = Bill.query.all()
    out = {}
    for b in bills:
        paid = sum([p.amount for p in b.payments]) if b.payments else 0.0
        due = round(b.total_amount - paid, 2)
        if due <= 0:
            continue
        pid = b.patient_id
        out.setdefault(pid, {"patient_id": pid, "patient_name": b.patient.name, "outstanding": 0.0})
        out[pid]["outstanding"] += due
    return jsonify(list(out.values())), 200
