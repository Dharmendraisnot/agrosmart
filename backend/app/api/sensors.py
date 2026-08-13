"""
Sensors API blueprint.

Endpoints:
    GET  /api/sensors/latest      — capture + return a fresh sensor reading
    GET  /api/sensors/history     — paginated history of past readings
    POST /api/sensors/reading     — manually submit a reading (testing / overrides)
"""
from __future__ import annotations

import logging
from flask import Blueprint, jsonify, request

from app.services.sensor_service import (
    capture_reading,
    get_latest_reading,
    get_reading_history,
)
from app.extensions import db
from app.models.sensor_reading import SensorReading

logger = logging.getLogger(__name__)

sensors_bp = Blueprint("sensors", __name__)


@sensors_bp.get("/sensors/latest")
def latest_reading():
    """
    Trigger a fresh sensor read (via HAL), persist it, and return the result.

    In simulator mode this generates a new simulated snapshot each call.
    In hardware mode this reads real sensors on the Pi.

    Response 200:
        { id, timestamp, source, moisture, ph, soil_temperature,
          air_temperature, air_humidity, nitrogen, phosphorus, potassium }
    """
    try:
        reading = capture_reading()
        return jsonify(reading.to_dict()), 200
    except Exception as exc:
        logger.error("Failed to capture sensor reading: %s", exc)
        return jsonify({"error": "Failed to read sensors", "detail": str(exc)}), 500


@sensors_bp.get("/sensors/history")
def reading_history():
    """
    Return a paginated list of past sensor readings (newest first).

    Query params:
        page     (int, default 1)
        per_page (int, default 50, max 200)
    """
    try:
        page     = max(1, request.args.get("page",     1,   type=int))
        per_page = min(200, max(1, request.args.get("per_page", 50, type=int)))
        result   = get_reading_history(page=page, per_page=per_page)
        return jsonify(result), 200
    except Exception as exc:
        logger.error("Failed to fetch sensor history: %s", exc)
        return jsonify({"error": "Failed to retrieve history", "detail": str(exc)}), 500


@sensors_bp.post("/sensors/reading")
def submit_reading():
    """
    Manually submit a sensor reading as JSON.
    Useful for testing the pipeline without triggering the HAL,
    and for injecting readings from external scripts.

    Request body (all fields optional — missing fields stored as NULL):
        {
            "moisture":         float,
            "ph":               float,
            "soil_temperature": float,
            "air_temperature":  float,
            "air_humidity":     float,
            "nitrogen":         float,
            "phosphorus":       float,
            "potassium":        float,
            "source":           str   (default: "manual")
        }

    Response 201: the created SensorReading record.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Validate that all provided numeric fields are actually numbers
    numeric_fields = [
        "moisture", "ph", "soil_temperature",
        "air_temperature", "air_humidity",
        "nitrogen", "phosphorus", "potassium",
    ]
    for field in numeric_fields:
        val = data.get(field)
        if val is not None and not isinstance(val, (int, float)):
            return jsonify({"error": f"Field '{field}' must be a number"}), 422

    reading = SensorReading(
        source           = str(data.get("source", "manual"))[:20],
        moisture         = data.get("moisture"),
        ph               = data.get("ph"),
        soil_temperature = data.get("soil_temperature"),
        air_temperature  = data.get("air_temperature"),
        air_humidity     = data.get("air_humidity"),
        nitrogen         = data.get("nitrogen"),
        phosphorus       = data.get("phosphorus"),
        potassium        = data.get("potassium"),
    )

    db.session.add(reading)
    db.session.commit()
    logger.info("Manual SensorReading id=%d submitted", reading.id)

    return jsonify(reading.to_dict()), 201
