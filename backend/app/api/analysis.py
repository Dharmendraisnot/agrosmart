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
      1. Reads sensors (via HAL/simulator)
      2. Runs crop / fertilizer / irrigation models
      3. Persists results to DB
      4. Returns full result JSON

    Optional JSON body:
        {
            "reading_id": int   — use an existing sensor reading instead of capturing fresh
        }

    Response 200: full analysis result
    Response 500: pipeline error details
    """
    data       = request.get_json(silent=True) or {}
    reading_id = data.get("reading_id")

    # Validate reading_id if provided
    if reading_id is not None:
        if not isinstance(reading_id, int) or reading_id < 1:
            return jsonify({"error": "reading_id must be a positive integer"}), 422

    try:
        result = run_analysis(reading_id=reading_id)
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
