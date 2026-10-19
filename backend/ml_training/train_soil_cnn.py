"""
train_soil_cnn.py — Train the CNN soil image classification model using MobileNetV2.

Architecture:
  - Base: MobileNetV2 (pretrained on ImageNet, weights frozen initially)
  - Head: GlobalAveragePooling2D + Dropout(0.3) + Dense(128, relu) + Dropout(0.2) + Dense(4, softmax)

Dataset:
  - 4 classes: Alluvial, Black, Clay, Red
  - Stored in: ml_training/datasets/soil_images/<Class>/
  - Preprocessing: MobileNetV2 preprocess_input (scales to [-1.0, 1.0])
  - Partitioning: Stratified 70% Train / 15% Validation / 15% Test
  - Audit: Strict hash verification asserting 0 duplicate or cross-split overlap

Training Phases:
  - Stage 1: Feature Extraction (Backbone frozen, train custom head only, 10 epochs, lr=1e-3)
  - Stage 2: Fine-Tuning (Top 20 backbone layers unfrozen, BatchNormalization kept FROZEN,
            10 epochs, lr=1e-4, ModelCheckpoint on val_loss, EarlyStopping)

Evaluation:
  - Evaluated on the held-out 15% Test set ONLY after model selection and best-weight restoration
  - Computes Accuracy, Precision, Recall, Macro F1, and Confusion Matrix

Outputs:
  - trained_models/soil_cnn_v1.h5        — trained best Keras model
  - trained_models/soil_cnn_classes.pkl  — class label list
  - trained_models/soil_cnn_metrics.json — test evaluation metrics & epoch logs
  - trained_models/soil_cnn_splits.json  — verified file and hash splits

Usage:
  python ml_training/train_soil_cnn.py            # Train and evaluate
  python ml_training/train_soil_cnn.py --inspect  # Print dataset & split counts only (no training)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split

# ── Path setup ────────────────────────────────────────────────────────────────
BACKEND_DIR   = Path(__file__).resolve().parent.parent
IMAGES_DIR    = BACKEND_DIR / "ml_training" / "datasets" / "soil_images"
MODELS_DIR    = BACKEND_DIR / "trained_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_OUT     = MODELS_DIR / "soil_cnn_v1.h5"
CLASSES_OUT   = MODELS_DIR / "soil_cnn_classes.pkl"
METRICS_OUT   = MODELS_DIR / "soil_cnn_metrics.json"
SPLITS_OUT    = MODELS_DIR / "soil_cnn_splits.json"

# ── Hyperparameters ───────────────────────────────────────────────────────────
IMG_SIZE        = (224, 224)   # MobileNetV2 default input resolution
BATCH_SIZE      = 32
EPOCHS_FROZEN   = 10           # Stage 1: head-only epochs
EPOCHS_FINETUNE = 10           # Stage 2: top backbone layers fine-tuning
SEED            = 42

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)


def compute_file_md5(path: Path) -> str:
    """Compute MD5 hash of an image file."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def load_dataset_catalog() -> tuple[pd.DataFrame, list[str]]:
    """Scan IMAGES_DIR, compute MD5 hashes, and return DataFrame + class names."""
    if not IMAGES_DIR.exists():
        logger.error(
            "Soil images directory not found at: %s\n"
            "Ensure the dataset is prepared under ml_training/datasets/soil_images/<Class>/",
            IMAGES_DIR,
        )
        sys.exit(1)

    classes = sorted([d.name for d in IMAGES_DIR.iterdir() if d.is_dir()])
    if len(classes) < 2:
        logger.error("Need at least 2 class subdirectories in %s, found: %s",
                     IMAGES_DIR, classes)
        sys.exit(1)

    records = []
    for c in classes:
        folder = IMAGES_DIR / c
        for img_path in folder.glob("*.*"):
            if img_path.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                records.append({
                    "filepath": str(img_path.resolve()),
                    "label": c,
                    "md5_hash": compute_file_md5(img_path),
                })

    df = pd.DataFrame(records)
    if df.empty:
        logger.error("No images found in %s", IMAGES_DIR)
        sys.exit(1)

    # Double-check: assert zero duplicates in catalog
    assert len(df) == df["md5_hash"].nunique(), (
        f"Internal error: found duplicate hashes in catalog! "
        f"{len(df)} files vs {df['md5_hash'].nunique()} unique hashes"
    )

    logger.info("Found %d total unique images across %d classes: %s", len(df), len(classes), classes)
    for c in classes:
        logger.info("  Class %-12s: %d images", c, len(df[df["label"] == c]))

    return df, classes


def create_stratified_splits(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split the dataset into Stratified 70% Train, 15% Validation, 15% Test.
    Strictly asserts zero exact-hash overlap between any two splits.
    """
    # 70% Train, 30% Temp (Val + Test)
    train_df, temp_df = train_test_split(
        df,
        test_size=0.30,
        random_state=SEED,
        stratify=df["label"],
    )

    # 30% Temp split evenly -> 15% Validation, 15% Test
    val_df, test_df = train_test_split(
        temp_df,
        test_size=0.50,
        random_state=SEED,
        stratify=temp_df["label"],
    )

    # Exact-hash overlap verification
    train_hashes = set(train_df["md5_hash"])
    val_hashes   = set(val_df["md5_hash"])
    test_hashes  = set(test_df["md5_hash"])

    assert len(train_hashes.intersection(val_hashes)) == 0, "Data leakage: Train and Val share hashes!"
    assert len(train_hashes.intersection(test_hashes)) == 0, "Data leakage: Train and Test share hashes!"
    assert len(val_hashes.intersection(test_hashes)) == 0, "Data leakage: Val and Test share hashes!"

    logger.info("Data leakage audit passed: Verified 0 hash overlap across Train, Val, and Test splits.")

    return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True)


def build_mobilenetv2_model(num_classes: int):
    """
    Build transfer learning model using MobileNetV2 pretrained on ImageNet.
    Pretrained backbone is frozen; only custom classification head is trainable in Stage 1.
    """
    import tensorflow as tf
    from tensorflow.keras import layers, Model
    from tensorflow.keras.applications import MobileNetV2

    base = MobileNetV2(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False   # Freeze pretrained weights

    inputs = tf.keras.Input(shape=(*IMG_SIZE, 3))
    x = base(inputs, training=False)
    x = layers.GlobalAveragePooling2D(name="global_avg_pool")(x)
    x = layers.Dropout(0.3, name="top_dropout_1")(x)
    x = layers.Dense(128, activation="relu", name="dense_128")(x)
    x = layers.Dropout(0.2, name="top_dropout_2")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="predictions")(x)

    model = Model(inputs, outputs, name="AgroSmart_MobileNetV2_SoilClassifier")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model, base


def get_generators(train_df: pd.DataFrame, val_df: pd.DataFrame,
                   test_df: pd.DataFrame, classes: list[str]):
    """
    Build training, validation, and test generators.
    Uses MobileNetV2 preprocess_input [-1.0, 1.0] scaling across all splits.
    Augmentation is applied ONLY to the training generator.
    """
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

    # Training generator with geometric data augmentation
    train_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_input,
        rotation_range=20,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
        vertical_flip=True,
        zoom_range=0.15,
    )

    # Validation and test: NO augmentation, deterministic MobileNetV2 scaling
    val_test_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_input,
    )

    train_gen = train_datagen.flow_from_dataframe(
        dataframe=train_df,
        x_col="filepath",
        y_col="label",
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        classes=classes,
        shuffle=True,
        seed=SEED,
    )

    val_gen = val_test_datagen.flow_from_dataframe(
        dataframe=val_df,
        x_col="filepath",
        y_col="label",
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        classes=classes,
        shuffle=False,
    )

    test_gen = val_test_datagen.flow_from_dataframe(
        dataframe=test_df,
        x_col="filepath",
        y_col="label",
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        classes=classes,
        shuffle=False,
    )

    return train_gen, val_gen, test_gen


def train_and_evaluate(train_df: pd.DataFrame, val_df: pd.DataFrame,
                       test_df: pd.DataFrame, classes: list[str]) -> tuple[object, dict]:
    """Execute Stage 1 (frozen base) and Stage 2 (fine-tuning with frozen BatchNorm), then evaluate on test set."""
    import tensorflow as tf

    model, base = build_mobilenetv2_model(len(classes))
    logger.info("MobileNetV2 Model built. Total parameters: %d", model.count_params())

    train_gen, val_gen, test_gen = get_generators(train_df, val_df, test_df, classes)

    # Best-model checkpoint callback monitoring validation loss
    checkpoint_cb = tf.keras.callbacks.ModelCheckpoint(
        filepath=str(MODEL_OUT),
        monitor="val_loss",
        save_best_only=True,
        mode="min",
        verbose=1,
    )

    callbacks_stage1 = [
        checkpoint_cb,
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=4, restore_best_weights=True, verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=2, min_lr=1e-6, verbose=1
        ),
    ]

    # ── Stage 1: Train classification head only (backbone frozen) ─────────────
    logger.info("=" * 70)
    logger.info("STAGE 1: Training Classification Head (Backbone Frozen, %d epochs)", EPOCHS_FROZEN)
    logger.info("=" * 70)
    history1 = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_FROZEN,
        callbacks=callbacks_stage1,
        verbose=1,
    )

    # ── Stage 2: Fine-tune top 20 layers of MobileNetV2 with frozen BatchNorm ──
    logger.info("=" * 70)
    logger.info("STAGE 2: Fine-Tuning Top 20 Backbone Layers (%d epochs)", EPOCHS_FINETUNE)
    logger.info("=" * 70)
    base.trainable = True

    # Freeze all layers except top 20
    for layer in base.layers[:-20]:
        layer.trainable = False

    # CRITICAL SAFEGUARD: Keep BatchNormalization layers frozen
    # This prevents updating running mean/variance on small batches and destabilizing pretrained statistics
    frozen_bn_count = 0
    for layer in base.layers:
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False
            frozen_bn_count += 1

    logger.info("Base layers configured: %d BatchNormalization layers explicitly FROZEN", frozen_bn_count)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks_stage2 = [
        checkpoint_cb,
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=4, restore_best_weights=True, verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=2, min_lr=1e-6, verbose=1
        ),
    ]

    history2 = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_FINETUNE,
        callbacks=callbacks_stage2,
        verbose=1,
    )

    # Ensure the model loaded into memory is the best checkpoint from disk
    logger.info("Loading best saved model checkpoint from %s for test evaluation...", MODEL_OUT)
    best_model = tf.keras.models.load_model(str(MODEL_OUT))

    # ── Stage 3: Final Independent Test Set Evaluation ────────────────────────
    logger.info("=" * 70)
    logger.info("STAGE 3: Evaluating Best Model on Held-Out Test Set (%d samples)", len(test_df))
    logger.info("=" * 70)

    test_loss, test_acc = best_model.evaluate(test_gen, verbose=0)
    y_pred_probs = best_model.predict(test_gen, verbose=0)
    y_pred = np.argmax(y_pred_probs, axis=1)
    y_true = test_gen.classes

    clf_report = classification_report(y_true, y_pred, target_names=classes, output_dict=True)
    clf_report_text = classification_report(y_true, y_pred, target_names=classes)
    conf_mat = confusion_matrix(y_true, y_pred).tolist()

    logger.info("\n" + clf_report_text)

    metrics = {
        "test_accuracy": round(float(test_acc), 4),
        "test_loss": round(float(test_loss), 4),
        "n_classes": len(classes),
        "classes": classes,
        "sample_counts": {
            "train": len(train_df),
            "val": len(val_df),
            "test": len(test_df),
            "total": len(train_df) + len(val_df) + len(test_df),
        },
        "stage1_history": {
            k: [round(float(v), 4) for v in vals]
            for k, vals in history1.history.items()
        },
        "stage2_history": {
            k: [round(float(v), 4) for v in vals]
            for k, vals in history2.history.items()
        },
        "classification_report": clf_report,
        "confusion_matrix": conf_mat,
        "architecture": "MobileNetV2 (pretrained on ImageNet) + custom head",
        "preprocessing": "MobileNetV2 preprocess_input [-1.0, 1.0]",
    }

    return best_model, metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train MobileNetV2 Soil Classifier")
    parser.add_argument("--inspect", action="store_true", help="Print dataset and split counts without training")
    args = parser.parse_args()

    logger.info("AgroSmart — Soil CNN Model Training (MobileNetV2)")

    df, classes = load_dataset_catalog()
    train_df, val_df, test_df = create_stratified_splits(df)

    # Save split records with MD5 hashes to trained_models/soil_cnn_splits.json
    splits_payload = {
        "summary": {
            "train": len(train_df),
            "val": len(val_df),
            "test": len(test_df),
            "total": len(df),
        },
        "class_counts": {
            c: {
                "train": int(len(train_df[train_df["label"] == c])),
                "val": int(len(val_df[val_df["label"] == c])),
                "test": int(len(test_df[test_df["label"] == c])),
                "total": int(len(df[df["label"] == c])),
            }
            for c in classes
        },
        "train_files": train_df[["filepath", "label", "md5_hash"]].to_dict(orient="records"),
        "val_files": val_df[["filepath", "label", "md5_hash"]].to_dict(orient="records"),
        "test_files": test_df[["filepath", "label", "md5_hash"]].to_dict(orient="records"),
    }
    with open(SPLITS_OUT, "w", encoding="utf-8") as f:
        json.dump(splits_payload, f, indent=2)
    logger.info("Saved verified split records and MD5 hashes to %s", SPLITS_OUT)

    logger.info("=" * 70)
    logger.info("STRATIFIED DATASET SPLIT SUMMARY (70 / 15 / 15)")
    logger.info("=" * 70)
    logger.info("%-12s | %-10s | %-10s | %-10s | %-10s", "Class", "Train (70%)", "Val (15%)", "Test (15%)", "Total")
    logger.info("-" * 70)
    for c in classes:
        n_train = len(train_df[train_df["label"] == c])
        n_val   = len(val_df[val_df["label"] == c])
        n_test  = len(test_df[test_df["label"] == c])
        n_total = n_train + n_val + n_test
        logger.info("%-12s | %-10d | %-10d | %-10d | %-10d", c, n_train, n_val, n_test, n_total)
    logger.info("-" * 70)
    logger.info("%-12s | %-10d | %-10d | %-10d | %-10d", "TOTAL",
                len(train_df), len(val_df), len(test_df), len(df))
    logger.info("=" * 70)

    if args.inspect:
        logger.info("Inspect mode complete. Model training was not run.")
        return

    # Train model and evaluate
    model, metrics = train_and_evaluate(train_df, val_df, test_df, classes)

    # Save artifacts
    joblib.dump(classes, CLASSES_OUT)
    with open(METRICS_OUT, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    logger.info("=" * 70)
    logger.info("SOIL CNN TRAINING COMPLETE")
    logger.info("=" * 70)
    logger.info("Test Accuracy : %.4f (%.1f%%)", metrics["test_accuracy"], metrics["test_accuracy"] * 100)
    logger.info("Test Loss     : %.4f", metrics["test_loss"])
    logger.info("Model saved   → %s", MODEL_OUT)
    logger.info("Classes saved → %s", CLASSES_OUT)
    logger.info("Metrics saved → %s", METRICS_OUT)
    logger.info("Splits saved  → %s", SPLITS_OUT)


if __name__ == "__main__":
    main()
