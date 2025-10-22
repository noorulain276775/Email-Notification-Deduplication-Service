from flask import Flask
from .config import DevConfig
from .extensions import db
from app.routes.emails import bp as emails_bp

def create_app(config_object=DevConfig):
    app = Flask(__name__)
    app.config.from_object(config_object)

    # init extensions
    db.init_app(app)

    # blueprints
    app.register_blueprint(emails_bp)

    # create tables (dev convenience)
    with app.app_context():
        db.create_all()

    return app
