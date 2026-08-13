"""
AgroSmart Flask application factory.

Usage:
    from app import create_app
    app = create_app()          # uses FLASK_ENV to pick config
    app = create_app("testing") # force a specific config
"""
import logging
import logging.handlers
from pathlib import Path

from flask import Flask

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
