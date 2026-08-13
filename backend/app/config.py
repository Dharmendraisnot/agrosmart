"""
Configuration classes for AgroSmart.
Selected via FLASK_ENV environment variable.
"""
import os
from pathlib import Path

# Absolute path to the backend/ directory
BASE_DIR = Path(__file__).resolve().parent.parent


class BaseConfig:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'instance' / 'agrosmart.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads
    UPLOAD_FOLDER = BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))  # 10 MB
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    # Sensor mode: "simulator" | "hardware"
    SENSOR_MODE = os.getenv("SENSOR_MODE", "simulator")

    # ML model paths (resolved relative to BASE_DIR)
    CROP_MODEL_PATH        = BASE_DIR / os.getenv("CROP_MODEL_PATH",        "trained_models/crop_rf_v1.pkl")
    SOIL_CNN_MODEL_PATH    = BASE_DIR / os.getenv("SOIL_CNN_MODEL_PATH",    "trained_models/soil_cnn_v1.h5")
    FERTILIZER_MODEL_PATH  = BASE_DIR / os.getenv("FERTILIZER_MODEL_PATH",  "trained_models/fertilizer_dt_prototype.pkl")
    FERTILIZER_MODEL_LABEL = os.getenv("FERTILIZER_MODEL_LABEL", "prototype_kaggle_v1.0")
    FEATURE_SCALER_PATH    = BASE_DIR / os.getenv("FEATURE_SCALER_PATH",    "trained_models/feature_scaler.pkl")
    LABEL_ENCODERS_PATH    = BASE_DIR / os.getenv("LABEL_ENCODERS_PATH",    "trained_models/label_encoders.pkl")

    # Logging
    LOG_DIR = BASE_DIR / "logs"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    # Use an in-memory SQLite DB for tests — never touches the real file
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # Silence WTF and other noise in tests
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False


_config_map = {
    "development": DevelopmentConfig,
    "testing":     TestingConfig,
    "production":  ProductionConfig,
}


def get_config() -> type:
    """Return the config class matching FLASK_ENV (default: development)."""
    env = os.getenv("FLASK_ENV", "development").lower()
    return _config_map.get(env, DevelopmentConfig)
