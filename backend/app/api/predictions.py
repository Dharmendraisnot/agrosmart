"""
Predictions API blueprint.

Endpoints:
    GET /api/predictions/latest     — most recent prediction set
    GET /api/predictions/<id>       — fetch one prediction record
    GET /api/predictions/history    — paginated prediction history
"""
from __future__ import annotations

import logging
from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models.prediction   import Prediction
from app.models.soil_analysis import SoilAnalysis

logger = logging.getLogger(__name__)

predictions_bp = Blueprint("predictions", __name__)


@predictions_bp.get("/predictions/latest")
def latest_predictions():
    """
    Return the three most recent prediction records (crop + fertilizer + irrigation)
    from the latest completed analysis.

    Response 200: { analysis_id, timestamp, crop, fertilizer, irrigation }
    Response 404: no predictions exist yet
    """
    # Find the most recent SoilAnalysis that has predictions
    latest_analysis = (
        db.session.query(SoilAnalysis)
        .order_by(SoilAnalysis.timestamp.desc())
        .first()
    )
    if latest_analysis is None:
        return jsonify({"error": "No analysis results found. Run POST /api/analysis/run first."}), 404

    predictions = {p.prediction_type: p.to_dict()
                   for p in latest_analysis.predictions}

    return jsonify({
        "analysis_id": latest_analysis.id,
        "timestamp":   latest_analysis.timestamp.isoformat(),
        "soil": {
            "type":          latest_analysis.soil_type,
            "health_status": latest_analysis.soil_health_status,
            "health_score":  latest_analysis.health_score,
        },
        "predictions": predictions,
    }), 200


@predictions_bp.get("/predictions/history")
def predictions_history():
    """
    Return a paginated list of all prediction records (newest first).

    Query params:
        page            (int, default 1)
        per_page        (int, default 20, max 100)
        prediction_type (str, optional — filter by "crop"/"fertilizer"/"irrigation")
    """
    page            = max(1, request.args.get("page",     1,  type=int))
    per_page        = min(100, max(1, request.args.get("per_page", 20, type=int)))
    pred_type_filter = request.args.get("prediction_type")

    query = db.session.query(Prediction).order_by(Prediction.timestamp.desc())

    if pred_type_filter in ("crop", "fertilizer", "irrigation"):
        query = query.filter(Prediction.prediction_type == pred_type_filter)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items":    [p.to_dict() for p in pagination.items],
        "total":    pagination.total,
        "page":     pagination.page,
        "per_page": pagination.per_page,
        "pages":    pagination.pages,
    }), 200


@predictions_bp.get("/predictions/<int:prediction_id>")
def get_prediction(prediction_id: int):
    """
    Fetch a single Prediction record by id.

    Response 200: prediction dict with full result JSON
    Response 404: not found
    """
    pred = db.session.get(Prediction, prediction_id)
    if pred is None:
        return jsonify({"error": f"Prediction id={prediction_id} not found"}), 404
    return jsonify(pred.to_dict()), 200
