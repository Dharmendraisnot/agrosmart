"""
evaluate_models.py — Unified evaluation report for all AgroSmart ML models.

Loads each saved model from trained_models/ and evaluates it against a
held-out test split of the relevant dataset. Prints a consolidated report.

Usage:
  python ml_training/evaluate_models.py [--model crop|fertilizer|cnn|all]

Options:
  --model crop        Evaluate only the crop Random Forest
  --model fertilizer  Evaluate only the fertilizer Decision Tree
  --model cnn         Evaluate only the soil CNN
  --model all         Evaluate all models (default)

NOTE: Evaluation metrics are computed fresh each run against real test data.
      Accuracy figures are never hardcoded in this script.
"""
from __future__ import annotations

import sys
import argparse
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
BACKEND_DIR  = Path(__file__).resolve().parent.parent
MODELS_DIR   = BACKEND_DIR / "trained_models"
DATASETS_DIR = BACKEND_DIR / "ml_training" / "datasets"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ── Crop model evaluation ─────────────────────────────────────────────────────

def evaluate_crop_model() -> None:
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

    model_path  = MODELS_DIR / "crop_rf_v1.pkl"
    scaler_path = MODELS_DIR / "crop_scaler.pkl"
    data_path   = DATASETS_DIR / "crop_recommendation.csv"

    if not model_path.exists():
        logger.warning("Crop model not found at %s — skipping.", model_path)
        return
    if not data_path.exists():
        logger.warning("Crop dataset not found at %s — skipping.", data_path)
        return

    logger.info("=" * 60)
    logger.info("CROP RECOMMENDATION MODEL  (crop_rf_v1.pkl)")
    logger.info("=" * 60)

    df     = pd.read_csv(data_path)
    FEATS  = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
    X      = df[FEATS].values
    y      = df["label"].values

    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2,
                                            random_state=42, stratify=y)

    model  = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    X_test_s = scaler.transform(X_test)
    y_pred   = model.predict(X_test_s)

    acc = accuracy_score(y_test, y_pred)
    logger.info("Test accuracy : %.4f  (%.1f%%)", acc, acc * 100)
    logger.info("Test samples  : %d", len(y_test))
    logger.info("Classes       : %d", len(np.unique(y)))
    logger.info("Feature importances (top 5):")
    importances = model.feature_importances_
    for feat, imp in sorted(zip(FEATS, importances), key=lambda x: -x[1])[:5]:
        logger.info("  %-15s  %.4f", feat, imp)
    logger.info("\nClassification Report:")
    print(classification_report(y_test, y_pred))


# ── Fertilizer model evaluation ───────────────────────────────────────────────

def evaluate_fertilizer_model() -> None:
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.preprocessing import LabelEncoder

    # Try final first, fall back to prototype
    for suffix in ("final", "prototype"):
        model_path = MODELS_DIR / f"fertilizer_dt_{suffix}.pkl"
        if model_path.exists():
            break
    else:
        logger.warning("No fertilizer model found in %s — skipping.", MODELS_DIR)
        return

    scaler_path  = MODELS_DIR / "fertilizer_scaler.pkl"
    encoder_path = MODELS_DIR / "fertilizer_encoders.pkl"
    data_path    = DATASETS_DIR / "fertilizer_recommendation.csv"

    if not data_path.exists():
        logger.warning("Fertilizer dataset not found at %s — skipping.", data_path)
        return

    logger.info("=" * 60)
    logger.info("FERTILIZER MODEL  (%s)  [%s]",
                model_path.name,
                "FINAL" if suffix == "final" else "⚠ PROTOTYPE — Kaggle data")
    logger.info("=" * 60)

    COLUMN_MAP = {
        "Temperature": "temperature", "Humidity": "humidity",
        "Moisture": "moisture", "Soil Type": "soil_type",
        "Crop Type": "crop_type", "Nitrogen": "nitrogen",
        "Potassium": "potassium", "Phosphorous": "phosphorus",
        "Fertilizer Name": "fertilizer_name",
    }
    FEATS = ["temperature", "humidity", "moisture",
             "soil_type", "crop_type", "nitrogen", "potassium", "phosphorus"]

    df = pd.read_csv(data_path).rename(columns=COLUMN_MAP)
    for col in ["soil_type", "crop_type", "fertilizer_name"]:
        df[col] = df[col].astype(str).str.strip()

    enc = joblib.load(encoder_path)
    df["soil_type"] = enc["soil_encoder"].transform(df["soil_type"])
    df["crop_type"] = enc["crop_encoder"].transform(df["crop_type"])

    X = df[FEATS].values.astype(float)
    y = df["fertilizer_name"].values

    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2,
                                            random_state=42, stratify=y)

    model  = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    X_test_s = scaler.transform(X_test)
    y_pred   = model.predict(X_test_s)

    acc = accuracy_score(y_test, y_pred)
    logger.info("Test accuracy : %.4f  (%.1f%%)", acc, acc * 100)
    logger.info("Test samples  : %d", len(y_test))
    logger.info("Tree depth    : %d", model.get_depth())
    logger.info("Tree leaves   : %d", model.get_n_leaves())
    logger.info("\nClassification Report:")
    print(classification_report(y_test, y_pred))


# ── CNN evaluation ────────────────────────────────────────────────────────────

def evaluate_cnn_model() -> None:
    model_path   = MODELS_DIR / "soil_cnn_v1.h5"
    classes_path = MODELS_DIR / "soil_cnn_classes.pkl"
    images_dir   = DATASETS_DIR / "soil_images"

    if not model_path.exists():
        logger.warning("CNN model not found at %s — skipping.", model_path)
        return
    if not images_dir.exists():
        logger.warning("Soil images not found at %s — skipping.", images_dir)
        return

    try:
        import tensorflow as tf
        from tensorflow.keras.preprocessing.image import ImageDataGenerator
    except ImportError:
        logger.warning("TensorFlow not installed — skipping CNN evaluation.")
        return

    logger.info("=" * 60)
    logger.info("SOIL IMAGE CNN MODEL  (soil_cnn_v1.h5)")
    logger.info("=" * 60)

    classes = joblib.load(classes_path)
    model   = tf.keras.models.load_model(str(model_path))

    datagen = ImageDataGenerator(
        rescale=1.0 / 255.0,
        validation_split=0.2,
    )
    val_gen = datagen.flow_from_directory(
        images_dir,
        target_size=(224, 224),
        batch_size=32,
        class_mode="categorical",
        subset="validation",
        seed=42,
        classes=classes,
    )

    val_loss, val_acc = model.evaluate(val_gen, verbose=0)
    logger.info("Classes       : %s", classes)
    logger.info("Val accuracy  : %.4f  (%.1f%%)", val_acc, val_acc * 100)
    logger.info("Val loss      : %.4f", val_loss)
    logger.info("Parameters    : %d", model.count_params())


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="AgroSmart model evaluation")
    parser.add_argument(
        "--model",
        choices=["crop", "fertilizer", "cnn", "all"],
        default="all",
    )
    args = parser.parse_args()

    logger.info("AgroSmart — Model Evaluation Report")
    logger.info("Models directory: %s", MODELS_DIR)

    if args.model in ("crop", "all"):
        evaluate_crop_model()
    if args.model in ("fertilizer", "all"):
        evaluate_fertilizer_model()
    if args.model in ("cnn", "all"):
        evaluate_cnn_model()

    logger.info("Evaluation complete.")


if __name__ == "__main__":
    main()
