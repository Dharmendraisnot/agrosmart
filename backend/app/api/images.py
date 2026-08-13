"""
Images API blueprint.

Endpoints:
    POST /api/images/upload      — upload a soil image, run CNN classification
    GET  /api/images/<filename>  — serve a previously uploaded image
"""
from __future__ import annotations

import logging
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file, current_app

from app.services.image_service import classify_image, get_upload_path

logger = logging.getLogger(__name__)

images_bp = Blueprint("images", __name__)


@images_bp.post("/images/upload")
def upload_image():
    """
    Upload a soil image and run CNN soil type classification.

    Request: multipart/form-data with field name "image"

    Optional form fields:
        run_analysis (bool, default false) — if "true", also trigger the full
            analysis pipeline using the CNN result (future integration hook,
            currently returns image result only)

    Response 200:
        {
          "filename":      "abc123_photo.jpg",
          "relative_path": "abc123_photo.jpg",
          "soil_type":     "Loamy",
          "confidence":    0.87,
          "all_classes":   [{"class": "Loamy", "confidence": 0.87}, ...],
          "cnn_status":    "ok" | "model_unavailable"
        }

    Response 400: no file in request
    Response 422: validation failure (bad extension, wrong MIME type)
    Response 500: unexpected error
    """
    if "image" not in request.files:
        return jsonify({"error": "No file field 'image' in request. "
                                 "Use multipart/form-data with field name 'image'."}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    try:
        result = classify_image(file)
        return jsonify(result), 200

    except ValueError as exc:
        # Validation errors (bad extension, MIME mismatch, etc.)
        return jsonify({"error": str(exc)}), 422

    except Exception as exc:
        logger.error("Image upload/classification error: %s", exc, exc_info=True)
        return jsonify({"error": "Image processing failed", "detail": str(exc)}), 500


@images_bp.get("/images/<path:filename>")
def serve_image(filename: str):
    """
    Serve a previously uploaded image by filename.

    The filename must be a plain filename (no directory separators).
    Path traversal attempts are blocked.

    Response 200: image file (as attachment)
    Response 404: file not found or path traversal attempt
    """
    # Block any path separators in the filename parameter
    if "/" in filename or "\\" in filename or ".." in filename:
        return jsonify({"error": "Invalid filename."}), 404

    path = get_upload_path(filename)
    if path is None:
        return jsonify({"error": f"Image '{filename}' not found."}), 404

    return send_file(str(path))
