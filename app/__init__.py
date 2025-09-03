"""SahAI application factory and app wiring (Step 3 adds CLI seed)."""
from __future__ import annotations
import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask, request
from .extensions import db, migrate, csrf, login_manager, limiter
from .routes import main_bp, register_error_pages
from .middleware.request_ids import register_request_id
from .logging_config import init_logging
from .errors.handlers import errors_bp
from . import model  # noqa: F401  # ensure Alembic sees models
from .auth.routes import auth_bp
from .user.routes import user_bp
from .services.seed_data import seed as seed_data
from .journal.routes import journal_bp
from .music.routes import music_bp
from .questions.routes import questions_bp
from .wellness.routes import wellness_bp
from .peer.routes import peer_bp
from .exam.routes import exam_bp
from .letters.routes import letters_bp
from .art.routes import art_bp
from .comics.routes import comics_bp
from .gratitude.routes import gratitude_bp
from .demo.routes import demo_bp
from .ai.health import ai_health_bp
from .cli.pitch import register_cli 
from .cli.pitch_full import register_cli_full
from .main.routes import about_bp
from .debug_tools import assert_unique_endpoints
from flask_wtf import CSRFProtect

csrf = CSRFProtect()

def create_app(config_object: str | object = "config.DevelopmentConfig") -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_object if isinstance(config_object, str) else config_object)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "9a714a5c8a8624ba")
    app.config["WTF_CSRF_SECRET_KEY"] = os.getenv("WTF_CSRF_SECRET_KEY", app.config["SECRET_KEY"])

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    # Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(about_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(journal_bp)
    app.register_blueprint(music_bp, url_prefix="")  
    app.register_blueprint(questions_bp, url_prefix="")
    app.register_blueprint(wellness_bp)
    app.register_blueprint(peer_bp)
    app.register_blueprint(exam_bp)
    app.register_blueprint(letters_bp)
    app.register_blueprint(art_bp)
    app.register_blueprint(comics_bp)
    app.register_blueprint(gratitude_bp, url_prefix="/gratitude")
    app.register_blueprint(demo_bp, url_prefix="/demo")
    app.register_blueprint(ai_health_bp)

    register_error_pages(app)
    register_request_id(app)
    app.register_blueprint(errors_bp)
    init_logging(app)

    # --- CLI: flask seed ---
    @app.cli.command("seed")
    def seed_cmd():
        """Seeds the database with safe demo content."""
        with app.app_context():
            seed_data()
            print("✅ Seeded demo data: user 'demo' / password 'demo1234'")

    # Security headers
    @app.after_request
    def set_security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("X-XSS-Protection", "1; mode=block")
        csp = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net https://cdn.jsdelivr.net/npm/ 'unsafe-inline'; "
            "style-src 'self' https://cdn.jsdelivr.net https://cdn.jsdelivr.net/npm/ 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' https://cdn.jsdelivr.net https://cdn.jsdelivr.net/npm/ data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        resp.headers.setdefault("Content-Security-Policy", csp)
        return resp

    register_cli(app)
    register_cli_full(app)

    # Dev safeguard for duplicate endpoints
    if app.debug or app.config.get("FLASK_ENV") == "development":
        try:
            assert_unique_endpoints(app)
        except AssertionError as e:
            app.logger.error(str(e))
            raise

    return app


def _configure_logging(app: Flask) -> None:
    """Rotating file + console logging."""
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    logfile = os.path.join(log_dir, "sahai.log")

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    file_handler = RotatingFileHandler(logfile, maxBytes=1_000_000, backupCount=5)
    file_handler.setLevel(app.config.get("LOG_LEVEL", "INFO"))
    file_handler.setFormatter(formatter)

    console = logging.StreamHandler()
    console.setLevel(app.config.get("LOG_LEVEL", "INFO"))
    console.setFormatter(formatter)

    # Avoid duplicate handlers during reloader
    app.logger.handlers = [file_handler, console]
    app.logger.setLevel(app.config.get("LOG_LEVEL", "INFO"))
