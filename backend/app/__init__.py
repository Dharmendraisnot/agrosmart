"""
AgroSmart Flask application factory.

Usage:
    from app import create_app
    app = create_app()          # uses FLASK_ENV to pick config
    app = create_app("testing") # force a specific config
"""
import logging
import logging.handlers
import os
from pathlib import Path

from flask import Flask, jsonify

from .config import get_config, BaseConfig
from .extensions import db, cors


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    # ── Load configuration ────────────────────────────────────────────────
    cfg = get_config() if config_name is None else _resolve_config(config_name)
    app.config.from_object(cfg)

    # ── Ensure required directories exist ────────────────────────────────
    _ensure_directories(app)

    # ── Initialise extensions ─────────────────────────────────────────────
    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # ── Register blueprints ───────────────────────────────────────────────
    _register_blueprints(app)

    # ── Register global error handlers ────────────────────────────────────
    _register_error_handlers(app)

    # ── Create database tables ────────────────────────────────────────────
    with app.app_context():
        # Import models so SQLAlchemy metadata is populated before create_all
        from .models import SensorReading, SoilAnalysis, Prediction, User  # noqa: F401
        db.create_all()

    # ── Configure logging ─────────────────────────────────────────────────
    _configure_logging(app)

    app.logger.info(
        "AgroSmart started | env=%s | sensor_mode=%s | db=%s",
        app.config.get("ENV", "development"),
        app.config.get("SENSOR_MODE"),
        app.config.get("SQLALCHEMY_DATABASE_URI"),
    )

    # ── Warmup CNN model in background thread ─────────────────────────────
    # Avoid duplicate execution in the Werkzeug reloader parent process or during unit tests
    if not app.config.get("TESTING"):
        if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            from .ml.soil_cnn import warmup_model
            warmup_model(app.config, async_mode=True)

    return app


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_config(name: str) -> type:
    from .config import DevelopmentConfig, TestingConfig, ProductionConfig
    mapping = {
        "development": DevelopmentConfig,
        "testing":     TestingConfig,
        "production":  ProductionConfig,
    }
    return mapping.get(name, DevelopmentConfig)


def _ensure_directories(app: Flask) -> None:
    """Create upload, log, trained_models, and instance directories if absent."""
    from .config import BASE_DIR
    dirs = [
        app.config["UPLOAD_FOLDER"],
        app.config["LOG_DIR"],
        BASE_DIR / "instance",
        BASE_DIR / "trained_models",
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def _register_blueprints(app: Flask) -> None:
    from .api.health       import health_bp
    from .api.sensors      import sensors_bp
    from .api.analysis     import analysis_bp
    from .api.predictions  import predictions_bp
    from .api.images       import images_bp
    app.register_blueprint(health_bp,      url_prefix="/api")
    app.register_blueprint(sensors_bp,     url_prefix="/api")
    app.register_blueprint(analysis_bp,    url_prefix="/api")
    app.register_blueprint(predictions_bp, url_prefix="/api")
    app.register_blueprint(images_bp,      url_prefix="/api")


def _register_error_handlers(app: Flask) -> None:
    """Register global JSON error handlers for HTTP and unexpected exceptions."""
    from werkzeug.exceptions import HTTPException

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested resource was not found.",
            },
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return jsonify({
            "success": False,
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "The method is not allowed for the requested URL.",
            },
        }), 405

    @app.errorhandler(413)
    def handle_payload_too_large(e):
        return jsonify({
            "success": False,
            "error": {
                "code": "PAYLOAD_TOO_LARGE",
                "message": "The uploaded file or request payload exceeds the allowed limit.",
            },
        }), 413

    @app.errorhandler(Exception)
    def handle_unhandled_exception(e):
        # Preserve Werkzeug HTTPExceptions with their specific status code and safe message
        if isinstance(e, HTTPException):
            code = e.code or 500
            code_str = (e.name or "HTTP_ERROR").upper().replace(" ", "_")
            if code >= 500:
                app.logger.error("HTTP server error %s: %s", code, e, exc_info=True)
            return jsonify({
                "success": False,
                "error": {
                    "code": code_str,
                    "message": e.description or str(e),
                },
            }), code

        # Log unexpected internal exceptions server-side with full traceback
        app.logger.error("Unhandled server exception: %s", e, exc_info=True)
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
            },
        }), 500


def _configure_logging(app: Flask) -> None:
    log_dir: Path = app.config["LOG_DIR"]
    log_file = log_dir / "agrosmart.log"

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )

    # Rotating file handler — max 5 MB, keep 3 backups
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    file_handler.setFormatter(formatter)

    # Stream handler for console output during development
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO"), logging.INFO)

    app.logger.setLevel(log_level)
    app.logger.addHandler(file_handler)

    if app.config.get("DEBUG"):
        app.logger.addHandler(stream_handler)
