"""
Shared preprocessing pipeline for AgroSmart tabular ML models.

Used by:
  - train_crop_model.py
  - train_fertilizer_model.py
  - app/ml/preprocessor.py  (inference time)

Responsibilities:
  - Define the canonical feature column order for each model.
  - Fit a StandardScaler and LabelEncoders on training data.
  - Provide transform() for inference (no re-fitting).
  - Save and load the fitted artefacts as .pkl files.
"""
from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder

logger = logging.getLogger(__name__)

# ── Canonical feature order ───────────────────────────────────────────────────
# These lists define the exact column order the models expect at inference time.
# Never change this order after a model is trained — it must stay in sync with
# how the model was fitted.

CROP_FEATURES = [
    "nitrogen", "phosphorus", "potassium",
    "temperature",   # soil temperature (°C)
    "humidity",      # air humidity (%)
    "ph",
    "rainfall",      # mapped from moisture for Kaggle dataset compatibility
]

FERTILIZER_FEATURES = [
    "temperature",   # air temperature
    "humidity",      # air humidity
    "moisture",      # soil moisture
    "soil_type",     # encoded integer
    "crop_type",     # encoded integer
    "nitrogen",
    "potassium",
    "phosphorus",
]


class CropPreprocessor:
    """
    Fits / transforms features for the Random Forest crop model.

    Kaggle Crop Recommendation dataset columns:
        N, P, K, temperature, humidity, ph, rainfall, label
    """

    def __init__(self):
        self.scaler: StandardScaler | None = None

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        """Fit scaler on training data and return scaled array."""
        X = df[CROP_FEATURES].values.astype(float)
        self.scaler = StandardScaler()
        return self.scaler.fit_transform(X)

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform without re-fitting — for inference."""
        if self.scaler is None:
            raise RuntimeError("CropPreprocessor has not been fitted yet. "
                               "Call fit_transform() first or load a saved scaler.")
        X = df[CROP_FEATURES].values.astype(float)
        return self.scaler.transform(X)

    def save(self, path: str | Path) -> None:
        joblib.dump(self.scaler, path)
        logger.info("CropPreprocessor scaler saved → %s", path)

    @classmethod
    def load(cls, path: str | Path) -> "CropPreprocessor":
        obj = cls()
        obj.scaler = joblib.load(path)
        logger.info("CropPreprocessor scaler loaded ← %s", path)
        return obj


class FertilizerPreprocessor:
    """
    Fits / transforms features for the Decision Tree fertilizer model.

    Kaggle Fertilizer Prediction dataset columns:
        Temperature, Humidity, Moisture, Soil Type, Crop Type,
        Nitrogen, Potassium, Phosphorous, Fertilizer Name
    """

    def __init__(self):
        self.scaler: StandardScaler | None = None
        self.soil_encoder: LabelEncoder | None = None
        self.crop_encoder: LabelEncoder | None = None

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        """Fit encoders + scaler and return transformed array."""
        df = df.copy()

        self.soil_encoder = LabelEncoder()
        self.crop_encoder = LabelEncoder()

        df["soil_type"] = self.soil_encoder.fit_transform(df["soil_type"].astype(str))
        df["crop_type"] = self.crop_encoder.fit_transform(df["crop_type"].astype(str))

        X = df[FERTILIZER_FEATURES].values.astype(float)
        self.scaler = StandardScaler()
        return self.scaler.fit_transform(X)

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform at inference time — encoders and scaler must be pre-loaded."""
        if self.scaler is None or self.soil_encoder is None:
            raise RuntimeError("FertilizerPreprocessor has not been fitted.")
        df = df.copy()
        df["soil_type"] = self.soil_encoder.transform(df["soil_type"].astype(str))
        df["crop_type"] = self.crop_encoder.transform(df["crop_type"].astype(str))
        X = df[FERTILIZER_FEATURES].values.astype(float)
        return self.scaler.transform(X)

    def save(self, scaler_path: str | Path, encoders_path: str | Path) -> None:
        joblib.dump(self.scaler, scaler_path)
        joblib.dump(
            {"soil_encoder": self.soil_encoder, "crop_encoder": self.crop_encoder},
            encoders_path,
        )
        logger.info("FertilizerPreprocessor saved → %s, %s", scaler_path, encoders_path)

    @classmethod
    def load(cls, scaler_path: str | Path, encoders_path: str | Path) -> "FertilizerPreprocessor":
        obj = cls()
        obj.scaler = joblib.load(scaler_path)
        enc = joblib.load(encoders_path)
        obj.soil_encoder = enc["soil_encoder"]
        obj.crop_encoder = enc["crop_encoder"]
        logger.info("FertilizerPreprocessor loaded ← %s, %s", scaler_path, encoders_path)
        return obj
