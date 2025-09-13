from flask import Flask
from .extensions import db, jwt, bcrypt
from .routes import register_blueprints
from config import Config, TestingConfig

config_map = {
    "default": Config,
    "testing": TestingConfig,
}

def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, Config))

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)

    # Register routes/blueprints
    register_blueprints(app)

    return app
