from flask import Blueprint

from .auth import auth_bp
from .patients import patients_bp
from .appointments import appointments_bp
from .doctors import doctors_bp
from .billings import billing_bp
from .beds import beds_bp
from .export_reports import export_bp

from .visualization import viz_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(patients_bp, url_prefix="/patients")
    app.register_blueprint(appointments_bp, url_prefix="/appointments")
    app.register_blueprint(doctors_bp, url_prefix="/doctors")
    app.register_blueprint(billing_bp, url_prefix="/billing")
    app.register_blueprint(beds_bp, url_prefix="/beds")
    app.register_blueprint(viz_bp, url_prefix="/visualization")
    app.register_blueprint(export_bp, url_prefix="/export")