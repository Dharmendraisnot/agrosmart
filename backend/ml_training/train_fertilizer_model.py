"""
train_fertilizer_model.py — Train the Decision Tree fertilizer recommendation model.

⚠  PROTOTYPE MODEL — trained on Kaggle data.
   This model exists to validate the software pipeline end-to-end.
   Once sufficient real AgroSmart sensor + field data is collected (Phase 5),
   re-run this script with the AgroSmart dataset to produce
   fertilizer_dt_final.pkl, which becomes the production model.

Dataset: Kaggle Fertilizer Prediction Dataset
  URL: https://www.kaggle.com/datasets/gdabhishek/fertilizer-prediction
  Place the CSV at: ml_training/datasets/fertilizer_recommendation.csv

Output (prototype):
  trained_models/fertilizer_dt_prototype.pkl   — fitted DecisionTreeClassifier
  trained_models/fertilizer_scaler.pkl         — fitted StandardScaler
  trained_models/fertilizer_encoders.pkl       — fitted LabelEncoders

Output (final — produced in Phase 5 with real data):
  trained_models/fertilizer_dt_final.pkl

Usage:
  python ml_training/train_fertilizer_model.py [--final]

  --final  : label output as final model (use only with AgroSmart collected data)
"""
from __future__ import annotations

import sys
import argparse
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report

# ── Path setup ────────────────────────────────────────────────────────────────
BACKEND_DIR  = Path(__file__).resolve().parent.parent
DATASET_PATH = BACKEND_DIR / "ml_training" / "datasets" / "fertilizer_recommendation.csv"
MODELS_DIR   = BACKEND_DIR / "trained_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Kaggle dataset column mappings ────────────────────────────────────────────
# Kaggle headers → internal canonical names
COLUMN_MAP = {
    "Temperature":   "temperature",
    "Humidity":      "humidity",
    "Moisture":      "moisture",
    "Soil Type":     "soil_type",
    "Crop Type":     "crop_type",
    "Nitrogen":      "nitrogen",
    "Potassium":     "potassium",
    "Phosphorous":   "phosphorus",
    "Fertilizer Name": "fertilizer_name",
}

FEATURE_COLS = [
    "temperature", "humidity", "moisture",
    "soil_type",   # label-encoded
    "crop_type",   # label-encoded
    "nitrogen", "potassium", "phosphorus",
]
TARGET_COL = "fertilizer_name"


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        logger.error(
            "Dataset not found: %s\n"
            "Download from: https://www.kaggle.com/datasets/gdabhishek/fertilizer-prediction\n"
            "and place it at: %s",
            path, path,
        )
        sys.exit(1)
    df = pd.read_csv(path)
    df.rename(columns=COLUMN_MAP, inplace=True)
    # Strip whitespace from string columns
    for col in ["soil_type", "crop_type", "fertilizer_name"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    logger.info("Loaded dataset: %d rows, %d columns", len(df), len(df.columns))
    return df


def train(df: pd.DataFrame) -> tuple[DecisionTreeClassifier, StandardScaler,
                                      LabelEncoder, LabelEncoder, dict]:
    """Fit the Decision Tree and return (model, scaler, soil_enc, crop_enc, metrics)."""
    df = df.copy()

    soil_encoder = LabelEncoder()
    crop_encoder = LabelEncoder()
    df["soil_type"] = soil_encoder.fit_transform(df["soil_type"])
    df["crop_type"] = crop_encoder.fit_transform(df["crop_type"])

    X = df[FEATURE_COLS].values.astype(float)
    y = df[TARGET_COL].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler    = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    logger.info("Training DecisionTreeClassifier…")
    model = DecisionTreeClassifier(
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        criterion="gini",
    )
    model.fit(X_train_s, y_train)

    y_pred = model.predict(X_test_s)
    acc    = accuracy_score(y_test, y_pred)

    X_all_s   = scaler.transform(X)
    cv_scores = cross_val_score(model, X_all_s, y, cv=5, scoring="accuracy", n_jobs=-1)

    metrics = {
        "test_accuracy":    round(float(acc), 4),
        "cv_mean_accuracy": round(float(cv_scores.mean()), 4),
        "cv_std":           round(float(cv_scores.std()),  4),
        "n_train":          len(X_train),
        "n_test":           len(X_test),
        "n_classes":        len(np.unique(y)),
        "tree_depth":       model.get_depth(),
        "tree_n_leaves":    model.get_n_leaves(),
    }

    return model, scaler, soil_encoder, crop_encoder, metrics


def print_metrics(metrics: dict, model: DecisionTreeClassifier,
                  scaler: StandardScaler, X_test_s, y_test) -> None:
    y_pred = model.predict(X_test_s)
    logger.info("=" * 60)
    logger.info("FERTILIZER MODEL (PROTOTYPE) — EVALUATION RESULTS")
    logger.info("⚠  Dataset: Kaggle — retrain with AgroSmart data for final model")
    logger.info("=" * 60)
    logger.info("Train samples  : %d", metrics["n_train"])
    logger.info("Test  samples  : %d", metrics["n_test"])
    logger.info("Test  accuracy : %.4f  (%.1f%%)", metrics["test_accuracy"],
                metrics["test_accuracy"] * 100)
    logger.info("CV-5 accuracy  : %.4f ± %.4f", metrics["cv_mean_accuracy"],
                metrics["cv_std"])
    logger.info("Tree depth     : %d", metrics["tree_depth"])
    logger.info("Tree leaves    : %d", metrics["tree_n_leaves"])
    logger.info("-" * 60)
    print(classification_report(y_test, y_pred))


def save_artefacts(model, scaler, soil_encoder, crop_encoder,
                   is_final: bool) -> None:
    suffix  = "final" if is_final else "prototype"
    m_path  = MODELS_DIR / f"fertilizer_dt_{suffix}.pkl"
    sc_path = MODELS_DIR / "fertilizer_scaler.pkl"
    en_path = MODELS_DIR / "fertilizer_encoders.pkl"

    joblib.dump(model,  m_path)
    joblib.dump(scaler, sc_path)
    joblib.dump({"soil_encoder": soil_encoder, "crop_encoder": crop_encoder}, en_path)

    logger.info("Model    saved → %s", m_path)
    logger.info("Scaler   saved → %s", sc_path)
    logger.info("Encoders saved → %s", en_path)

    if not is_final:
        logger.info("REMINDER: This is a prototype model (Kaggle data).")
        logger.info("Set FERTILIZER_MODEL_PATH=trained_models/fertilizer_dt_prototype.pkl in .env")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train AgroSmart fertilizer model")
    parser.add_argument("--final", action="store_true",
                        help="Label output as final model (use with AgroSmart data only)")
    args = parser.parse_args()

    label = "FINAL (AgroSmart data)" if args.final else "PROTOTYPE (Kaggle data)"
    logger.info("AgroSmart — Fertilizer Recommendation Model Training  [%s]", label)

    df = load_dataset(DATASET_PATH)
    model, scaler, soil_enc, crop_enc, metrics = train(df)

    # Re-derive test split for printing
    df2 = df.copy()
    soil_enc2 = LabelEncoder(); crop_enc2 = LabelEncoder()
    df2["soil_type"] = soil_enc2.fit_transform(df2["soil_type"])
    df2["crop_type"] = crop_enc2.fit_transform(df2["crop_type"])
    X = df2[FEATURE_COLS].values.astype(float)
    y = df2[TARGET_COL].values
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2,
                                            random_state=42, stratify=y)
    X_test_s = scaler.transform(X_test)

    print_metrics(metrics, model, scaler, X_test_s, y_test)
    save_artefacts(model, scaler, soil_enc, crop_enc, is_final=args.final)
    logger.info("Training complete.")


if __name__ == "__main__":
    main()
