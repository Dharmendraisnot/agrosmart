"""
ml/crop_model.py — Random Forest crop recommendation inference wrapper.

Loads crop_rf_v1.pkl and crop_scaler.pkl at first use (lazy load).
Returns the top-N predicted crops with probability scores.

Usage:
    from app.ml.crop_model import predict_crops
    results = predict_crops(sensor_dict, top_n=3)
    # [{"crop": "wheat", "confidence": 0.82}, ...]
"""
from __future__ import annotations

import logging
from pathlib import Path
from functools import lru_cache

import joblib
import numpy as np

from app.ml.preprocessor import CropInferencePreprocessor

logger = logging.getLogger(__name__)

# ── Module-level lazy-loaded singletons ───────────────────────────────────────
_model      = None
_preprocessor: CropInferencePreprocessor | None = None


def _load(config) -> None:
    """Load model + scaler from paths defined in app config. Called once."""
    global _model, _preprocessor
    model_path  = Path(config["CROP_MODEL_PATH"])
    scaler_path = Path(config["CROP_MODEL_PATH"]).parent / "crop_scaler.pkl"

    if not model_path.exists():
        raise FileNotFoundError(
            f"Crop model not found: {model_path}\n"
            "Run: python ml_training/train_crop_model.py"
        )
    _model        = joblib.load(model_path)
    _preprocessor = CropInferencePreprocessor(scaler_path)
    logger.info("Crop RF model loaded from %s", model_path)


def predict_crops(sensor: dict, config: dict, top_n: int = 3) -> list[dict]:
    """
    Predict the top-N most suitable crops for the given soil/climate conditions.

    Args:
        sensor: dict with keys moisture, ph, soil_temperature, air_temperature,
                air_humidity, nitrogen, phosphorus, potassium
        config: Flask app.config dict (provides model paths)
        top_n:  number of top crops to return (default 3)

    Returns:
        List of dicts ordered by confidence (descending):
        [{"crop": "wheat", "confidence": 0.82, "rank": 1}, ...]
    """
    global _model, _preprocessor
    if _model is None:
        _load(config)

    X = _preprocessor.transform(sensor)
    probas  = _model.predict_proba(X)[0]
    classes = _model.classes_

    # Sort by probability descending, take top_n
    top_indices = np.argsort(probas)[::-1][:top_n]
    results = []
    for rank, idx in enumerate(top_indices, start=1):
        results.append({
            "crop":       str(classes[idx]),
            "confidence": round(float(probas[idx]), 4),
            "rank":       rank,
        })

    logger.debug("Crop prediction top-%d: %s", top_n, results)
    return results


def reload_model() -> None:
    """Force a model reload on the next predict call (use after retraining)."""
    global _model, _preprocessor
    _model        = None
    _preprocessor = None
    logger.info("Crop model cache cleared — will reload on next call")
