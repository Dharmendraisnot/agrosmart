"""
Health check endpoint.
GET /api/health → returns system status and current sensor mode.
"""
import os
from flask import Blueprint, jsonify, current_app

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    """
    Returns 200 with basic system information.
    The frontend and monitoring tools can poll this to confirm the backend is up.
    """
    return jsonify({
        "status":      "ok",
        "service":     "AgroSmart API",
        "version":     "1.0.0",
        "sensor_mode": current_app.config.get("SENSOR_MODE", "simulator"),
        "environment": os.getenv("FLASK_ENV", "development"),
    }), 200
