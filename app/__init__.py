# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_migrate import Migrate
from config import Config
import random

db = SQLAlchemy()
bcrypt = Bcrypt()
sess = Session()
migrate = Migrate()

def create_app():
    app = Flask(
        __name__,
        static_folder="../static",      # static folder at project root
        template_folder="templates"     # templates inside app/templates
    )

    # Load config
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    sess.init_app(app)
    migrate.init_app(app, db)

    # Register main user routes
    from app.routes import main
    app.register_blueprint(main)

    # ✅ Register admin routes (NO silent error)
    from app.admin_routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Jinja helpers
    app.jinja_env.globals['random'] = random.random
    app.jinja_env.globals['int'] = int

    return app
