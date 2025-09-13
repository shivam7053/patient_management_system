from .extensions import db, bcrypt
from datetime import datetime
 
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="staff")  # staff/admin/doctor

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    type = db.Column(db.String(20), default="outpatient")  # outpatient / inpatient
    diagnosis = db.Column(db.String(200), nullable=True)
    admitted_on = db.Column(db.DateTime, default=datetime.utcnow)
    is_admitted = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Patient {self.name}>"
    
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    doctor_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Scheduled")  # Scheduled / Completed / Cancelled

    patient = db.relationship("Patient", backref="appointments")

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)

    def __repr__(self):
        return f"<Doctor {self.name} - {self.specialization}>"
    
class Bill(db.Model):
    __tablename__ = "bill"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointment.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="pending")  # pending / partial / paid / cancelled
    currency = db.Column(db.String(10), default="INR")
    notes = db.Column(db.Text, nullable=True)

    patient = db.relationship("Patient", backref="bills")
    appointment = db.relationship("Appointment", backref="bills")
    items = db.relationship("BillItem", backref="bill", cascade="all, delete-orphan")
    payments = db.relationship("Payment", backref="bill", cascade="all, delete-orphan")

class BillItem(db.Model):
    __tablename__ = "bill_item"
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey("bill.id"), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, default=0.0)

    @property
    def amount(self):
        return (self.quantity or 0) * (self.unit_price or 0.0)

class Payment(db.Model):
    __tablename__ = "payment"
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey("bill.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(30), nullable=False)  # cash/card/upi/insurance
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    reference = db.Column(db.String(120), nullable=True)  # txn id etc.

class Bed(db.Model):
    __tablename__ = "bed"
    id = db.Column(db.Integer, primary_key=True)
    bed_number = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default="available")  # available / occupied / maintenance
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=True)
    assigned_at = db.Column(db.DateTime, nullable=True)

    patient = db.relationship("Patient", backref="bed", uselist=False)
