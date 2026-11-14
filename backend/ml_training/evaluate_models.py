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
import json
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

def evaluate_cnn_model(
    split: str = "test",
    splits_file: Path | None = None,
    clean_dir: Path | None = None,
    model_path: Path | None = None,
    classes_path: Path | None = None,
) -> dict | None:
    """
    Evaluates the saved MobileNetV2 CNN model against the clean dataset and official splits.

    Loads images strictly from: ml_training/datasets/soil_images_clean/
    Uses official split metadata: trained_models/soil_cnn_splits_v2.json
    Applies deterministic MobileNetV2 preprocessing ([-1.0, 1.0]) with zero augmentation.
    """
    if model_path is None:
        model_path = MODELS_DIR / "soil_cnn_v1.h5"
    else:
        model_path = Path(model_path)

    if classes_path is None:
        classes_path = MODELS_DIR / "soil_cnn_classes.pkl"
    else:
        classes_path = Path(classes_path)

    if splits_file is None:
        splits_file = MODELS_DIR / "soil_cnn_splits_v2.json"
        if not splits_file.exists():
            splits_file = MODELS_DIR / "soil_cnn_splits.json"
            logger.warning("soil_cnn_splits_v2.json not found — falling back to %s", splits_file)

    if clean_dir is None:
        clean_dir = DATASETS_DIR / "soil_images_clean"
        if not clean_dir.exists():
            clean_dir = DATASETS_DIR / "soil_images"
            logger.warning("soil_images_clean not found — falling back to %s", clean_dir)

    if not model_path.exists():
        logger.warning("CNN model not found at %s — skipping.", model_path)
        return None
    if not splits_file.exists():
        logger.warning("Split file not found at %s — skipping.", splits_file)
        return None

    try:
        import tensorflow as tf
        from PIL import Image
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score,
            f1_score, confusion_matrix, classification_report
        )
    except ImportError as exc:
        logger.warning("Required ML libraries not installed (%s) — skipping CNN evaluation.", exc)
        return None

    logger.info("=" * 60)
    logger.info("SOIL IMAGE CNN MODEL  (%s)", model_path.name)
    logger.info("Splits metadata : %s", splits_file.name)
    logger.info("Image source    : %s", clean_dir.name)
    logger.info("Target split    : %s", split.upper())
    logger.info("=" * 60)

    classes = joblib.load(classes_path)
    class_to_idx = {c: i for i, c in enumerate(classes)}

    with open(splits_file, "r", encoding="utf-8") as f:
        splits_data = json.load(f)

    # Cross-split overlap integrity check
    train_paths = set(item.get("relative_path", item.get("filepath")) for item in splits_data.get("train_files", []))
    val_paths   = set(item.get("relative_path", item.get("filepath")) for item in splits_data.get("val_files", []))
    test_paths  = set(item.get("relative_path", item.get("filepath")) for item in splits_data.get("test_files", []))

    if train_paths and test_paths:
        assert len(train_paths & test_paths) == 0, "Data leakage detected: overlap between train and test splits!"
    if train_paths and val_paths:
        assert len(train_paths & val_paths) == 0, "Data leakage detected: overlap between train and val splits!"
    if val_paths and test_paths:
        assert len(val_paths & test_paths) == 0, "Data leakage detected: overlap between val and test splits!"

    # Select target split list
    split_key = f"{split.lower()}_files"
    if split_key not in splits_data:
        raise ValueError(f"Unknown split '{split}'. Available: train, val, test")

    target_files = splits_data[split_key]
    if len(target_files) == 0:
        raise ValueError(f"Target split '{split}' is empty in {splits_file}")

    # Load and preprocess all target images deterministically
    images = []
    y_true = []
    skipped_count = 0

    for item in target_files:
        rel_p = item.get("relative_path")
        if rel_p and (clean_dir / rel_p).exists():
            img_path = clean_dir / rel_p
        elif Path(item["filepath"]).exists():
            img_path = Path(item["filepath"])
        else:
            raise FileNotFoundError(f"Split image missing from disk: {item.get('filepath') or rel_p}")

        label = item["label"]
        if label not in class_to_idx:
            raise ValueError(f"Unknown label '{label}' in split item (valid classes: {classes})")

        with Image.open(img_path) as img:
            rgb_img = img.convert("RGB").resize((224, 224), Image.Resampling.LANCZOS)
            arr = (np.array(rgb_img, dtype=np.float32) / 127.5) - 1.0
            images.append(arr)
        y_true.append(class_to_idx[label])

    model = tf.keras.models.load_model(str(model_path))
    x = np.array(images, dtype=np.float32)
    preds = model.predict(x, verbose=0)
    y_pred = np.argmax(preds, axis=1)

    # Loss calculation
    y_one_hot = tf.keras.utils.to_categorical(y_true, num_classes=len(classes))
    loss = float(tf.keras.losses.categorical_crossentropy(y_one_hot, preds).numpy().mean())

    acc = float(accuracy_score(y_true, y_pred))
    prec_macro = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    rec_macro = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    f1_macro = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    f1_weighted = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
    cm = confusion_matrix(y_true, y_pred, labels=range(len(classes)))
    report = classification_report(y_true, y_pred, target_names=classes, output_dict=True)

    logger.info("Split evaluated: %s (n=%d, skipped=%d)", split.upper(), len(target_files), skipped_count)
    logger.info("Loss           : %.4f", loss)
    logger.info("Accuracy       : %.4f (%.2f%%)", acc, acc * 100)
    logger.info("Macro Precision: %.4f", prec_macro)
    logger.info("Macro Recall   : %.4f", rec_macro)
    logger.info("Macro F1-Score : %.4f", f1_macro)
    logger.info("Weighted F1    : %.4f", f1_weighted)
    logger.info("\nClassification Report:\n%s", classification_report(y_true, y_pred, target_names=classes))
    logger.info("\nConfusion Matrix (%s):\n%s", classes, cm)

    return {
        "split": split,
        "splits_file": str(splits_file),
        "clean_dir": str(clean_dir),
        "total_evaluated": len(target_files),
        "total_skipped": skipped_count,
        "classes": classes,
        "loss": loss,
        "accuracy": acc,
        "macro_precision": prec_macro,
        "macro_recall": rec_macro,
        "macro_f1": f1_macro,
        "weighted_f1": f1_weighted,
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="AgroSmart model evaluation")
    parser.add_argument(
        "--model",
        choices=["crop", "fertilizer", "cnn", "all"],
        default="all",
    )
    parser.add_argument(
        "--split",
        choices=["train", "val", "test", "all"],
        default="test",
        help="Split to evaluate for CNN (default: test)",
    )
    args = parser.parse_args()

    logger.info("AgroSmart — Model Evaluation Report")
    logger.info("Models directory: %s", MODELS_DIR)

    if args.model in ("crop", "all"):
        evaluate_crop_model()
    if args.model in ("fertilizer", "all"):
        evaluate_fertilizer_model()
    if args.model in ("cnn", "all"):
        if args.split == "all":
            logger.info("\n>>> Evaluating Validation Split:")
            evaluate_cnn_model(split="val")
            logger.info("\n>>> Evaluating Held-Out Test Split:")
            evaluate_cnn_model(split="test")
        else:
            evaluate_cnn_model(split=args.split)

    logger.info("Evaluation complete.")


if __name__ == "__main__":
    main()
