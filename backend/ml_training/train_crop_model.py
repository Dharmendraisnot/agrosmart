"""
train_crop_model.py — Train the Random Forest crop recommendation model.

Dataset: Kaggle Crop Recommendation Dataset
  URL: https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset
  Place the CSV at: ml_training/datasets/crop_recommendation.csv

Output:
  trained_models/crop_rf_v1.pkl       — fitted RandomForestClassifier
  trained_models/crop_scaler.pkl      — fitted StandardScaler for crop features

Usage:
  python ml_training/train_crop_model.py

NOTE: This script trains on Kaggle data for pipeline development.
In Phase 5, supplement with locally collected AgroSmart sensor readings
and re-run to produce crop_rf_v2.pkl.
"""
from __future__ import annotations

import sys
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

# ── Path setup ────────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BACKEND_DIR / "ml_training" / "datasets" / "crop_recommendation.csv"
MODELS_DIR   = BACKEND_DIR / "trained_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_OUT   = MODELS_DIR / "crop_rf_v1.pkl"
SCALER_OUT  = MODELS_DIR / "crop_scaler.pkl"

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Feature columns (Kaggle dataset headers) ──────────────────────────────────
FEATURE_COLS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
TARGET_COL   = "label"


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        logger.error(
            "Dataset not found: %s\n"
            "Download from: https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset\n"
            "and place it at: %s",
            path, path,
        )
        sys.exit(1)
    df = pd.read_csv(path)
    logger.info("Loaded dataset: %d rows, %d columns", len(df), len(df.columns))
    return df


def train(df: pd.DataFrame) -> tuple[RandomForestClassifier, object, dict]:
    """
    Fit a RandomForestClassifier and return (model, scaler, metrics_dict).
    """
    from sklearn.preprocessing import StandardScaler

    X = df[FEATURE_COLS].values
    y = df[TARGET_COL].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale features
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    # Train Random Forest
    logger.info("Training RandomForestClassifier (100 trees)…")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        min_samples_split=2,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train_s, y_train)

    # Evaluate on held-out test set
    y_pred  = model.predict(X_test_s)
    acc     = accuracy_score(y_test, y_pred)
    report  = classification_report(y_test, y_pred, output_dict=True)

    # 5-fold cross-validation on full scaled data
    X_all_s = scaler.transform(X)
    cv_scores = cross_val_score(model, X_all_s, y, cv=5, scoring="accuracy", n_jobs=-1)

    metrics = {
        "test_accuracy":    round(float(acc), 4),
        "cv_mean_accuracy": round(float(cv_scores.mean()), 4),
        "cv_std":           round(float(cv_scores.std()),  4),
        "n_train":          len(X_train),
        "n_test":           len(X_test),
        "n_classes":        len(model.classes_),
        "classes":          list(model.classes_),
    }

    return model, scaler, metrics


def print_metrics(metrics: dict, model: RandomForestClassifier,
                  scaler, X_test_s, y_test) -> None:
    logger.info("=" * 60)
    logger.info("CROP RECOMMENDATION MODEL — EVALUATION RESULTS")
    logger.info("=" * 60)
    logger.info("Train samples  : %d", metrics["n_train"])
    logger.info("Test  samples  : %d", metrics["n_test"])
    logger.info("Classes        : %d  (%s)", metrics["n_classes"],
                ", ".join(metrics["classes"][:5]) + "…")
    logger.info("Test  accuracy : %.4f  (%.1f%%)", metrics["test_accuracy"],
                metrics["test_accuracy"] * 100)
    logger.info("CV-5 accuracy  : %.4f ± %.4f", metrics["cv_mean_accuracy"],
                metrics["cv_std"])
    logger.info("-" * 60)
    logger.info("Classification report (test set):")
    y_pred = model.predict(X_test_s)
    print(classification_report(y_test, y_pred))


def save_artefacts(model, scaler) -> None:
    joblib.dump(model,  MODEL_OUT)
    joblib.dump(scaler, SCALER_OUT)
    logger.info("Model  saved → %s", MODEL_OUT)
    logger.info("Scaler saved → %s", SCALER_OUT)


def main() -> None:
    logger.info("AgroSmart — Crop Recommendation Model Training")
    logger.info("Dataset: %s", DATASET_PATH)

    df = load_dataset(DATASET_PATH)

    # Basic sanity check
    missing = [c for c in FEATURE_COLS + [TARGET_COL] if c not in df.columns]
    if missing:
        logger.error("Missing columns in dataset: %s", missing)
        sys.exit(1)

    model, scaler, metrics = train(df)

    # Re-derive test split for printing (same seed → same split)
    from sklearn.preprocessing import StandardScaler as SS
    X = df[FEATURE_COLS].values
    y = df[TARGET_COL].values
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2,
                                            random_state=42, stratify=y)
    sc = SS(); sc.fit(X)
    X_test_s = sc.transform(X_test)

    print_metrics(metrics, model, scaler, X_test_s, y_test)
    save_artefacts(model, scaler)
    logger.info("Training complete.")


if __name__ == "__main__":
    main()
