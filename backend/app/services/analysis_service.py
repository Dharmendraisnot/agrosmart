"""
services/analysis_service.py — Full analysis pipeline orchestrator.

Flow:
  1. Capture fresh sensor reading (via HAL or use an existing SensorReading id)
  2. Run CNN soil classification (if image provided / model available)
  3. Compute soil health score from sensor values
  4. Run Random Forest → top-3 crop predictions
  5. Run Decision Tree → fertilizer recommendation
  6. Run rule engine   → irrigation advice
  7. Persist SoilAnalysis + three Prediction records
  8. Return consolidated result dict

This service coordinates everything but does not import Flask routes —
it only needs app context for DB access and config.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from flask import current_app

from app.extensions import db
from app.models.sensor_reading import SensorReading
from app.models.soil_analysis  import SoilAnalysis
from app.models.prediction     import Prediction
from app.services.sensor_service import capture_reading
from app.ml.crop_model        import predict_crops
from app.ml.fertilizer_model  import predict_fertilizer
from app.services.recommendation_service import generate_irrigation_advice

logger = logging.getLogger(__name__)


# ── Soil health scoring ───────────────────────────────────────────────────────

def _compute_health_score(sensor: dict, soil_type: str | None) -> tuple[float, str]:
    """
    Compute a 0–100 composite soil health score and a qualitative label.

    Scoring components (equal weight):
      - pH in optimal range (6.0–7.5)   : 0–25 pts
      - Moisture adequacy (35–65%)       : 0–25 pts
      - NPK adequacy                     : 0–25 pts
      - Temperature suitability          : 0–25 pts
    """
    score = 0.0

    # pH score (optimal 6.0–7.5)
    ph = sensor.get("ph")
    if ph is not None:
        if 6.0 <= ph <= 7.5:
            score += 25.0
        elif 5.5 <= ph < 6.0 or 7.5 < ph <= 8.0:
            score += 15.0
        elif 5.0 <= ph < 5.5 or 8.0 < ph <= 8.5:
            score += 8.0
        # else: very acidic/alkaline → 0 pts

    # Moisture score (optimal 35–65%)
    moisture = sensor.get("moisture")
    if moisture is not None:
        if 35.0 <= moisture <= 65.0:
            score += 25.0
        elif 25.0 <= moisture < 35.0 or 65.0 < moisture <= 75.0:
            score += 15.0
        elif 15.0 <= moisture < 25.0 or 75.0 < moisture <= 85.0:
            score += 8.0

    # NPK score — award points if at least two of N/P/K are in healthy ranges
    n = sensor.get("nitrogen");  p = sensor.get("phosphorus"); k = sensor.get("potassium")
    npk_ok = sum([
        n is not None and 20 <= n <= 80,
        p is not None and 10 <= p <= 50,
        k is not None and 80 <= k <= 280,
    ])
    score += {0: 0, 1: 8, 2: 17, 3: 25}.get(npk_ok, 0)

    # Temperature score (soil temp optimal 15–35°C)
    temp = sensor.get("soil_temperature")
    if temp is not None:
        if 15.0 <= temp <= 35.0:
            score += 25.0
        elif 10.0 <= temp < 15.0 or 35.0 < temp <= 40.0:
            score += 15.0
        elif 5.0 <= temp < 10.0 or 40.0 < temp <= 45.0:
            score += 8.0

    score = round(min(100.0, max(0.0, score)), 1)

    if score >= 70:
        label = "Good"
    elif score >= 45:
        label = "Fair"
    else:
        label = "Poor"

    return score, label


# ── Main orchestrator ─────────────────────────────────────────────────────────

def run_analysis(reading_id: int | None = None,
                 image_path: str | None = None,
                 cnn_result: dict | None = None) -> dict:
    """
    Run the full analysis pipeline and persist results to DB.

    Args:
        reading_id: use an existing SensorReading (if None, captures a fresh one)
        image_path: relative path of an uploaded soil image (optional)
        cnn_result: pre-computed CNN result dict from image_service (optional)

    Returns:
        Consolidated analysis result dict suitable for the API response.
    """
    config = current_app.config

    # ── Step 1: get sensor reading ────────────────────────────────────────────
    if reading_id is not None:
        reading = db.session.get(SensorReading, reading_id)
        if reading is None:
            raise ValueError(f"SensorReading id={reading_id} not found")
    else:
        reading = capture_reading()

    sensor = reading.to_dict()

    # ── Step 2: soil type from CNN (or fallback) ──────────────────────────────
    if cnn_result and cnn_result.get("status") == "ok":
        soil_type  = cnn_result["soil_type"]
        cnn_conf   = cnn_result["confidence"]
    else:
        # CNN unavailable — use a heuristic from sensor data as fallback
        soil_type = _heuristic_soil_type(sensor)
        cnn_conf  = None

    # ── Step 3: health score ──────────────────────────────────────────────────
    health_score, health_status = _compute_health_score(sensor, soil_type)

    # ── Step 4: crop prediction ───────────────────────────────────────────────
    try:
        crop_results = predict_crops(sensor, config, top_n=3)
        top_crop     = crop_results[0]["crop"] if crop_results else "wheat"
        crop_version = f"rf_v{_model_version(config['CROP_MODEL_PATH'])}"
    except Exception as exc:
        logger.error("Crop prediction failed: %s", exc)
        crop_results = []
        top_crop     = "wheat"
        crop_version = "error"

    # ── Step 5: fertilizer recommendation ────────────────────────────────────
    try:
        fert_result  = predict_fertilizer(sensor, soil_type, top_crop, config)
        fert_version = fert_result.get("model_label", "unknown")
    except Exception as exc:
        logger.error("Fertilizer prediction failed: %s", exc)
        fert_result  = {"fertilizer": "N/A", "advice": "Model unavailable", "model_label": "error"}
        fert_version = "error"

    # ── Step 6: irrigation advice ─────────────────────────────────────────────
    irrigation_result = generate_irrigation_advice(sensor, soil_type, top_crop)

    # ── Step 7: persist SoilAnalysis ─────────────────────────────────────────
    analysis = SoilAnalysis(
        timestamp            = datetime.now(timezone.utc),
        sensor_reading_id    = reading.id,
        soil_image_path      = image_path,
        soil_type            = soil_type,
        soil_type_confidence = cnn_conf,
        soil_health_status   = health_status,
        health_score         = health_score,
    )
    db.session.add(analysis)
    db.session.flush()   # populate analysis.id without committing yet

    # ── Step 8: persist three Prediction rows ────────────────────────────────
    pred_crop = Prediction(
        analysis_id       = analysis.id,
        prediction_type   = "crop",
        top_recommendation= top_crop,
        model_version     = crop_version,
    )
    pred_crop.result = {
        "crops":          crop_results,
        "sensor_reading": reading.id,
    }

    pred_fert = Prediction(
        analysis_id       = analysis.id,
        prediction_type   = "fertilizer",
        top_recommendation= fert_result.get("fertilizer", "N/A"),
        model_version     = fert_version,
    )
    pred_fert.result = fert_result

    pred_irr = Prediction(
        analysis_id       = analysis.id,
        prediction_type   = "irrigation",
        top_recommendation= irrigation_result.get("action", ""),
        model_version     = "rule_v1.0",
    )
    pred_irr.result = irrigation_result

    db.session.add_all([pred_crop, pred_fert, pred_irr])
    db.session.commit()

    logger.info(
        "Analysis id=%d complete | soil=%s | health=%s (%.1f) | crop=%s | fert=%s",
        analysis.id, soil_type, health_status, health_score,
        top_crop, fert_result.get("fertilizer"),
    )

    # ── Step 9: build response dict ───────────────────────────────────────────
    return {
        "analysis_id":    analysis.id,
        "timestamp":      analysis.timestamp.isoformat(),
        "sensor_reading": sensor,
        "soil": {
            "type":            soil_type,
            "type_confidence": cnn_conf,
            "health_status":   health_status,
            "health_score":    health_score,
        },
        "crops":       crop_results,
        "fertilizer":  fert_result,
        "irrigation":  irrigation_result,
        "prediction_ids": {
            "crop":       pred_crop.id,
            "fertilizer": pred_fert.id,
            "irrigation": pred_irr.id,
        },
    }


def get_analysis(analysis_id: int) -> dict | None:
    """Fetch a single analysis + its predictions from DB."""
    analysis = db.session.get(SoilAnalysis, analysis_id)
    if analysis is None:
        return None
    return _analysis_to_dict(analysis)


def get_analysis_history(page: int = 1, per_page: int = 20) -> dict:
    """Return paginated analysis history (newest first)."""
    pagination = (
        db.session.query(SoilAnalysis)
        .order_by(SoilAnalysis.timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return {
        "items":    [_analysis_to_dict(a) for a in pagination.items],
        "total":    pagination.total,
        "page":     pagination.page,
        "per_page": pagination.per_page,
        "pages":    pagination.pages,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _heuristic_soil_type(sensor: dict) -> str:
    """
    Simple heuristic soil type estimation from sensor values.
    Used as a fallback when the CNN model is unavailable.

    Returns soil type names that are compatible with both:
      - The fertilizer encoder classes (Black, Clayey, Loamy, Red, Sandy)
      - The CNN class names (Sandy, Clay, Loamy, Silty) used in Phase 5
    The fertilizer preprocessor handles unseen labels gracefully, so the
    CNN-style names (Clay, Silty) are acceptable — they fall back to index 0.
    """
    moisture = sensor.get("moisture", 50.0) or 50.0
    ph       = sensor.get("ph", 6.5) or 6.5

    if moisture > 65:
        return "Clayey"   # matches fertilizer encoder AND is clay-like
    if moisture < 30:
        return "Sandy"    # matches both encoders
    if 5.5 <= ph <= 7.0 and 35 <= moisture <= 65:
        return "Loamy"    # matches both encoders
    return "Loamy"        # safe default — always in fertilizer encoder


def _model_version(model_path) -> str:
    """Extract version string from model filename e.g. crop_rf_v1.pkl → 1."""
    from pathlib import Path
    stem = Path(model_path).stem   # e.g. "crop_rf_v1"
    if "_v" in stem:
        return stem.split("_v")[-1]
    return "1"


def _analysis_to_dict(analysis: SoilAnalysis) -> dict:
    """Serialise a SoilAnalysis with its linked predictions."""
    predictions = {}
    for pred in analysis.predictions:
        predictions[pred.prediction_type] = pred.to_dict()

    d = analysis.to_dict()
    d["predictions"] = predictions
    return d
