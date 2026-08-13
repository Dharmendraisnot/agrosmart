"""
ml/preprocessor.py — Inference-time feature preprocessing.

Loads the fitted scalers/encoders from trained_models/ and transforms
raw sensor dict values into the numpy arrays the models expect.

Feature order contracts (must match training scripts exactly):

  Crop model  : [nitrogen, phosphorus, potassium, temperature,
                 humidity, ph, rainfall]
                Where:
                  temperature = soil_temperature (°C)
                  humidity    = air_humidity (%)
                  rainfall    = moisture (%)  ← Kaggle proxy at inference

  Fertilizer  : [temperature, humidity, moisture, soil_type,
                 crop_type, nitrogen, potassium, phosphorus]
                Where:
                  temperature = air_temperature
                  soil_type   = label-encoded string (e.g. "Loamy")
                  crop_type   = label-encoded string (e.g. "Wheat")
"""
from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np

logger = logging.getLogger(__name__)

# ── Fallback median values used when a sensor reading is NULL ─────────────────
# Sourced from the training dataset distributions. Updated here if retraining
# changes the dataset significantly.
_CROP_MEDIANS = {
    "nitrogen":   40.0,
    "phosphorus": 25.0,
    "potassium":  180.0,
    "temperature": 26.0,
    "humidity":    62.0,
    "ph":           6.5,
    "rainfall":    52.0,   # moisture proxy
}

_FERT_MEDIANS = {
    "temperature": 28.0,
    "humidity":    60.0,
    "moisture":    50.0,
    "nitrogen":    40.0,
    "potassium":   45.0,
    "phosphorus":  22.0,
}


class CropInferencePreprocessor:
    """Loads the saved StandardScaler and transforms a sensor dict → numpy array."""

    def __init__(self, scaler_path: Path):
        self._scaler = joblib.load(scaler_path)
        logger.info("CropInferencePreprocessor loaded scaler from %s", scaler_path)

    def transform(self, sensor: dict) -> np.ndarray:
        """
        Map a sensor reading dict to the 7-feature crop model input vector.

        Missing / None values are replaced with training-set median values
        so inference still works when a sensor is unavailable (e.g. NPK
        sensor not yet connected).
        """
        def _get(key: str, fallback_key: str | None = None) -> float:
            v = sensor.get(key)
            if v is None and fallback_key:
                v = sensor.get(fallback_key)
            return float(v) if v is not None else _CROP_MEDIANS[key]

        row = np.array([[
            _get("nitrogen"),
            _get("phosphorus"),
            _get("potassium"),
            _get("temperature",  "soil_temperature"),
            _get("humidity",     "air_humidity"),
            _get("ph"),
            _get("rainfall",     "moisture"),   # moisture is our rainfall proxy
        ]])
        return self._scaler.transform(row)


class FertilizerInferencePreprocessor:
    """
    Loads saved StandardScaler + LabelEncoders and transforms a
    sensor+context dict → numpy array for the fertilizer Decision Tree.
    """

    def __init__(self, scaler_path: Path, encoders_path: Path):
        self._scaler   = joblib.load(scaler_path)
        enc            = joblib.load(encoders_path)
        self._soil_enc = enc["soil_encoder"]
        self._crop_enc = enc["crop_encoder"]
        logger.info("FertilizerInferencePreprocessor loaded from %s, %s",
                    scaler_path, encoders_path)

    def _encode_safe(self, encoder, value: str, default_idx: int = 0) -> int:
        """Encode a label; fall back to default_idx if unseen at training time."""
        classes = list(encoder.classes_)
        if value in classes:
            return int(encoder.transform([value])[0])
        logger.warning("Unseen label '%s' for encoder (classes: %s) — using index %d",
                       value, classes, default_idx)
        return default_idx

    def transform(self, sensor: dict, soil_type: str = "Loamy",
                  crop_type: str = "Wheat") -> np.ndarray:
        """
        Args:
            sensor:    raw sensor reading dict
            soil_type: CNN-predicted soil type string (e.g. "Loamy")
            crop_type: top-1 crop recommendation (e.g. "Wheat")
        """
        def _get(key: str, fallback_key: str | None = None) -> float:
            v = sensor.get(key)
            if v is None and fallback_key:
                v = sensor.get(fallback_key)
            return float(v) if v is not None else _FERT_MEDIANS.get(key, 0.0)

        soil_idx = self._encode_safe(self._soil_enc, soil_type)
        crop_idx = self._encode_safe(self._crop_enc, crop_type)

        row = np.array([[
            _get("temperature", "air_temperature"),
            _get("humidity",    "air_humidity"),
            _get("moisture"),
            float(soil_idx),
            float(crop_idx),
            _get("nitrogen"),
            _get("potassium"),
            _get("phosphorus"),
        ]])
        return self._scaler.transform(row)
