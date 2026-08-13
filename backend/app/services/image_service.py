"""
services/image_service.py — Soil image upload handling and CNN preprocessing.

Responsibilities:
  1. Validate uploaded file (extension, MIME sniff, max size)
  2. Save file to uploads/ with a secure, collision-safe filename
  3. Preprocess the image for CNN inference:
       - Decode with OpenCV (or Pillow fallback if OpenCV unavailable)
       - Resize to 224×224
       - Normalise pixel values to [0, 1]
  4. Call soil_cnn.predict_soil_type() and return the result dict

OpenCV is an optional dependency (not installed on all dev machines).
When OpenCV is absent, Pillow is used for all image operations.
"""
from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import IO

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import numpy as np

from app.ml.soil_cnn import predict_soil_type

logger = logging.getLogger(__name__)

# Allowed file extensions (lowercase)
_ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

# Target CNN input size
_CNN_SIZE = (224, 224)


# ── Validation ─────────────────────────────────────────────────────────────────

def _allowed_extension(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in _ALLOWED_EXTENSIONS
    )


def _sniff_mime(data: bytes) -> bool:
    """
    Check the first 12 bytes for known image magic numbers.
    Returns True if the file looks like a supported image format.
    """
    # JPEG: FF D8 FF
    # PNG:  89 50 4E 47 0D 0A 1A 0A
    # WebP: 52 49 46 46 ?? ?? ?? ?? 57 45 42 50
    if data[:3] == b"\xff\xd8\xff":
        return True
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return True
    return False


# ── Saving ──────────────────────────────────────────────────────────────────────

def save_upload(file: FileStorage) -> Path:
    """
    Validate and save an uploaded FileStorage object to the uploads directory.

    Returns:
        Absolute Path to the saved file.

    Raises:
        ValueError: if the file fails validation.
        IOError:    if the file cannot be written.
    """
    if not file or not file.filename:
        raise ValueError("No file provided.")

    if not _allowed_extension(file.filename):
        raise ValueError(
            f"File type not allowed. Accepted: {', '.join(_ALLOWED_EXTENSIONS)}"
        )

    # Read first 12 bytes for MIME sniff, then seek back
    header = file.read(12)
    file.seek(0)

    if not _sniff_mime(header):
        raise ValueError(
            "File content does not match a recognised image format "
            "(JPEG, PNG, WebP)."
        )

    upload_dir: Path = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Build a safe, unique filename: <uuid4>_<original_safe_name>
    safe_name    = secure_filename(file.filename)
    unique_name  = f"{uuid.uuid4().hex}_{safe_name}"
    dest         = upload_dir / unique_name

    file.save(str(dest))
    logger.info("Image saved: %s (%d bytes)", dest, dest.stat().st_size)
    return dest


# ── Preprocessing ───────────────────────────────────────────────────────────────

def _load_and_preprocess_opencv(path: Path) -> np.ndarray:
    """Use OpenCV to load + resize + normalise."""
    import cv2
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"OpenCV could not decode image: {path}")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, _CNN_SIZE, interpolation=cv2.INTER_AREA)
    return img.astype(np.float32) / 255.0


def _load_and_preprocess_pillow(path: Path) -> np.ndarray:
    """Pillow fallback — used when OpenCV is not installed."""
    from PIL import Image
    img = Image.open(path).convert("RGB")
    img = img.resize(_CNN_SIZE, Image.LANCZOS)
    return np.array(img, dtype=np.float32) / 255.0


def preprocess_image(path: Path) -> np.ndarray:
    """
    Load an image file and preprocess it for CNN inference.

    Returns:
        numpy array of shape (224, 224, 3), dtype float32, values in [0, 1]
    """
    try:
        import cv2  # noqa: F401
        return _load_and_preprocess_opencv(path)
    except ImportError:
        logger.debug("OpenCV not available — using Pillow for image preprocessing.")
        return _load_and_preprocess_pillow(path)


# ── Main entry point ───────────────────────────────────────────────────────────

def classify_image(file: FileStorage) -> dict:
    """
    Save an uploaded image, preprocess it, and run CNN soil classification.

    Args:
        file: Werkzeug FileStorage from request.files

    Returns:
        {
          "filename":        "abc123_photo.jpg",
          "relative_path":   "abc123_photo.jpg",   ← relative to uploads/
          "soil_type":       "Loamy",              ← None if model unavailable
          "confidence":      0.87,                 ← None if model unavailable
          "all_classes":     [...],
          "cnn_status":      "ok" | "model_unavailable",
        }

    Raises:
        ValueError: file validation failure (caller returns 422)
    """
    config = current_app.config

    # 1. Save
    dest = save_upload(file)

    # 2. Preprocess
    try:
        image_array = preprocess_image(dest)
    except Exception as exc:
        logger.error("Image preprocessing failed for %s: %s", dest, exc)
        # Return partial result — file saved but CNN not run
        return {
            "filename":      dest.name,
            "relative_path": dest.name,
            "soil_type":     None,
            "confidence":    None,
            "all_classes":   [],
            "cnn_status":    "preprocessing_failed",
            "error":         str(exc),
        }

    # 3. CNN inference
    cnn_result = predict_soil_type(image_array, config)

    return {
        "filename":      dest.name,
        "relative_path": dest.name,
        "soil_type":     cnn_result.get("soil_type"),
        "confidence":    cnn_result.get("confidence"),
        "all_classes":   cnn_result.get("all_classes", []),
        "cnn_status":    cnn_result.get("status", "unknown"),
    }


def get_upload_path(filename: str) -> Path | None:
    """
    Resolve a filename to its absolute path in the uploads directory.
    Returns None if the file does not exist or if the path escapes the
    uploads directory (path traversal guard).
    """
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    target     = (upload_dir / secure_filename(filename)).resolve()

    # Path traversal guard: ensure target is inside uploads/
    if not str(target).startswith(str(upload_dir)):
        logger.warning("Path traversal attempt blocked: %s", filename)
        return None

    return target if target.exists() else None
