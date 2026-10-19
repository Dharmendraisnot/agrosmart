"""
Analysis API blueprint.

Endpoints:
    POST /api/analysis/run        — trigger full analysis pipeline
    GET  /api/analysis/<id>       — fetch one analysis result
    GET  /api/analysis/history    — paginated analysis history
"""
from __future__ import annotations

import logging
from flask import Blueprint, jsonify, request

from app.services.analysis_service import (
    run_analysis,
    get_analysis,
    get_analysis_history,
)

logger = logging.getLogger(__name__)

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.post("/analysis/run")
def run_analysis_endpoint():
    """
    Trigger a complete soil analysis pipeline:
      1. Uses manual sensor data if provided, or reads existing reading_id,
         or generates fresh simulated parameters
      2. Runs crop / fertilizer / irrigation models
      3. Persists results to DB
      4. Returns full result JSON

    Optional JSON body:
        {
            "reading_id": int,              — use an existing sensor reading
            "sensor_data": {                — manual soil & environmental parameters
                "nitrogen": float,
                "phosphorus": float,
                "potassium": float,
                "ph": float,
                "moisture": float,
                "soil_temperature": float,
                "air_temperature": float,
                "air_humidity": float,
                "source": str
            },
            "soil_type": str,               — user-specified or CNN-derived soil type
            "image_path": str,              — path or filename of uploaded soil image
            "notes": str                    — optional analysis notes
        }

    Response 200: full analysis result
    Response 422: validation error
    Response 500: pipeline error details
    """
    data                   = request.get_json(silent=True) or {}
    reading_id             = data.get("reading_id")
    sensor_data            = data.get("sensor_data")
    soil_type              = data.get("soil_type")
    confirmed_soil_texture = data.get("confirmed_soil_texture") or data.get("confirmed_texture")
    image_path             = data.get("image_path") or data.get("image_filename")
    notes                  = data.get("notes")

    # Validate reading_id if provided
    if reading_id is not None:
        if not isinstance(reading_id, int) or reading_id < 1:
            return jsonify({"error": "reading_id must be a positive integer"}), 422

    # Validate sensor_data if provided
    if sensor_data is not None:
        if not isinstance(sensor_data, dict):
            return jsonify({"error": "sensor_data must be a dictionary"}), 422
        numeric_fields = [
            "moisture", "rainfall", "ph", "soil_temperature",
            "air_temperature", "air_humidity",
            "nitrogen", "phosphorus", "potassium",
            "temperature", "temp", "humidity",
        ]
        for field in numeric_fields:
            val = sensor_data.get(field)
            if val is not None and not isinstance(val, (int, float)):
                return jsonify({"error": f"Field '{field}' in sensor_data must be a number"}), 422

    # Validate soil_type if provided
    if soil_type is not None:
        if not isinstance(soil_type, str) or not soil_type.strip():
            return jsonify({"error": "soil_type must be a non-empty string"}), 422
        soil_type = soil_type.strip()

    # Validate confirmed_soil_texture if provided
    if confirmed_soil_texture is not None:
        if not isinstance(confirmed_soil_texture, str) or not confirmed_soil_texture.strip():
            return jsonify({"error": "confirmed_soil_texture must be a non-empty string"}), 422
        confirmed_soil_texture = confirmed_soil_texture.strip()

    try:
        result = run_analysis(
            reading_id=reading_id,
            sensor_data=sensor_data,
            soil_type=soil_type,
            confirmed_soil_texture=confirmed_soil_texture,
            image_path=image_path,
            notes=notes,
        )
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        logger.error("Analysis pipeline error: %s", exc, exc_info=True)
        return jsonify({"error": "Analysis failed", "detail": str(exc)}), 500


@analysis_bp.get("/analysis/history")
def analysis_history():
    """
    Return paginated analysis history (newest first).

    Query params:
        page     (int, default 1)
        per_page (int, default 20, max 100)
    """
    page     = max(1, request.args.get("page",     1,  type=int))
    per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))
    try:
        result = get_analysis_history(page=page, per_page=per_page)
        return jsonify(result), 200
    except Exception as exc:
        logger.error("Failed to fetch analysis history: %s", exc)
        return jsonify({"error": "Failed to retrieve history", "detail": str(exc)}), 500


@analysis_bp.get("/analysis/<int:analysis_id>")
def get_analysis_endpoint(analysis_id: int):
    """
    Fetch a single analysis record with all linked predictions.

    Response 200: analysis dict with embedded predictions
    Response 404: analysis not found
    """
    result = get_analysis(analysis_id)
    if result is None:
        return jsonify({"error": f"Analysis id={analysis_id} not found"}), 404
    return jsonify(result), 200
