"""
ml/fertilizer_model.py — Fertilizer recommendation inference wrapper.

Supports two model lifecycle stages (set via config):
  prototype_kaggle_v1.0  →  fertilizer_dt_prototype.pkl  (Kaggle data)
  final_agrosmart_v1.0   →  fertilizer_dt_final.pkl       (real AgroSmart data)

The active model is selected by FERTILIZER_MODEL_PATH in .env / config.py.
To switch, change FERTILIZER_MODEL_PATH and FERTILIZER_MODEL_LABEL — nothing
else in the codebase needs to change.

Usage:
    from app.ml.fertilizer_model import predict_fertilizer
    result = predict_fertilizer(sensor_dict, soil_type, top_crop, config)
"""
from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np

from app.ml.preprocessor import FertilizerInferencePreprocessor

logger = logging.getLogger(__name__)

_model        = None
_preprocessor: FertilizerInferencePreprocessor | None = None
_model_label  = None


def _load(config: dict) -> None:
    """Load model + scaler + encoders. Called once per process."""
    global _model, _preprocessor, _model_label

    model_path    = Path(config["FERTILIZER_MODEL_PATH"])
    scaler_path   = model_path.parent / "fertilizer_scaler.pkl"
    encoders_path = model_path.parent / "fertilizer_encoders.pkl"
    _model_label  = config.get("FERTILIZER_MODEL_LABEL", "unknown")

    if not model_path.exists():
        raise FileNotFoundError(
            f"Fertilizer model not found: {model_path}\n"
            "Run: python ml_training/train_fertilizer_model.py"
        )

    _model        = joblib.load(model_path)
    _preprocessor = FertilizerInferencePreprocessor(scaler_path, encoders_path)
    logger.info("Fertilizer model loaded from %s  [label=%s]",
                model_path, _model_label)


# ── Human-readable NPK advice keyed by fertilizer name ────────────────────────
_FERTILIZER_ADVICE = {
    "Urea":      "Apply 50 kg/acre. Urea is high in nitrogen — ideal for leafy growth.",
    "DAP":       "Apply 50 kg/acre. DAP provides phosphorus for root development.",
    "14-35-14":  "Apply 50 kg/acre. Balanced with high phosphorus for flowering crops.",
    "28-28":     "Apply 40 kg/acre. Equal N and P — good for general crop health.",
    "17-17-17":  "Apply 50 kg/acre. Fully balanced NPK for maintenance fertilisation.",
    "20-20":     "Apply 45 kg/acre. Balanced N and P — suitable for most soil types.",
    "10-26-26":  "Apply 50 kg/acre. High P and K — ideal for fruiting and root crops.",
}


def predict_fertilizer(sensor: dict, soil_type: str,
                       top_crop: str, config: dict) -> dict:
    """
    Predict the recommended fertilizer for the given soil + crop combination.

    Args:
        sensor:    sensor reading dict
        soil_type: CNN-predicted soil type (e.g. "Loamy")
        top_crop:  top-1 crop recommendation (e.g. "wheat")
        config:    Flask app.config dict

    Returns:
        {
          "fertilizer":   "17-17-17",
          "advice":       "Apply 50 kg/acre...",
          "model_label":  "prototype_kaggle_v1.0",
          "soil_type":    "Loamy",
          "crop":         "wheat",
        }
    """
    global _model, _preprocessor, _model_label
    if _model is None:
        _load(config)

    # Normalise crop name for the encoder (title-case matches training data)
    crop_norm = top_crop.title()

    X = _preprocessor.transform(sensor, soil_type=soil_type, crop_type=crop_norm)
    prediction   = _model.predict(X)[0]
    fertilizer   = str(prediction)
    advice       = _FERTILIZER_ADVICE.get(
        fertilizer, f"Apply {fertilizer} as directed on the product label."
    )

    result = {
        "fertilizer":  fertilizer,
        "advice":      advice,
        "model_label": _model_label,
        "soil_type":   soil_type,
        "crop":        top_crop,
    }
    logger.debug("Fertilizer prediction: %s", result)
    return result


def reload_model() -> None:
    """Force model reload on the next predict call."""
    global _model, _preprocessor, _model_label
    _model = _preprocessor = _model_label = None
    logger.info("Fertilizer model cache cleared — will reload on next call")
