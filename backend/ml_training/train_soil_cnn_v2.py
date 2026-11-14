"""
train_soil_cnn_v2.py — Retrain and optimize MobileNetV2 Soil Classifier
Phase 6, Task P1.3 — AgroSmart

Features:
  - Uses clean, leakage-free dataset: ml_training/datasets/soil_images_clean/
  - Uses official splits: trained_models/soil_cnn_splits_v2.json
  - Solves Clay recall issue via balanced class weights and moderate augmentation.
  - Two-stage transfer learning: Stage 1 frozen base, Stage 2 gentle fine-tuning
    with BatchNormalization layers strictly frozen.
  - ModelCheckpoint on val_loss ensures no degraded overfitted weights are retained.
  - Saves all artifacts as v2:
      trained_models/soil_cnn_v2.h5
      trained_models/soil_cnn_v2_classes.pkl
      trained_models/soil_cnn_v2_metrics.json
  - Evaluates on the held-out test split (n=71) and compares against v1 baseline.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from pathlib import Path

import joblib
import numpy as np
from PIL import Image
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.utils.class_weight import compute_class_weight

# ── Paths ─────────────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent
CLEAN_DIR = BACKEND_DIR / "ml_training" / "datasets" / "soil_images_clean"
MODELS_DIR = BACKEND_DIR / "trained_models"
SPLITS_PATH = MODELS_DIR / "soil_cnn_splits_v2.json"
CLASSES_PATH = MODELS_DIR / "soil_cnn_classes.pkl"

MODEL_V2_OUT = MODELS_DIR / "soil_cnn_v2.h5"
CLASSES_V2_OUT = MODELS_DIR / "soil_cnn_v2_classes.pkl"
METRICS_V2_OUT = MODELS_DIR / "soil_cnn_v2_metrics.json"

IMG_SIZE = (224, 224)
BATCH_SIZE = 16
SEED = 42

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    import tensorflow as tf
    tf.random.set_seed(seed)


def load_dataset_from_splits(splits_file: Path, clean_dir: Path, classes: list[str]):
    """Loads images into normalized memory arrays for train, val, and test splits."""
    with open(splits_file, "r", encoding="utf-8") as f:
        splits_data = json.load(f)

    class_to_idx = {c: i for i, c in enumerate(classes)}

    def _load_split(split_key):
        items = splits_data[split_key]
        x_list = []
        y_list = []
        for it in items:
            p = clean_dir / it["relative_path"]
            if not p.exists():
                p = Path(it["filepath"])
            with Image.open(p) as img:
                rgb_img = img.convert("RGB").resize(IMG_SIZE, Image.Resampling.LANCZOS)
                # Preprocess to [-1.0, 1.0]
                arr = (np.array(rgb_img, dtype=np.float32) / 127.5) - 1.0
                x_list.append(arr)
            y_list.append(class_to_idx[it["label"]])
        return np.array(x_list, dtype=np.float32), np.array(y_list, dtype=np.int32)

    logger.info("Loading splits from %s...", splits_file.name)
    x_train, y_train = _load_split("train_files")
    x_val, y_val = _load_split("val_files")
    x_test, y_test = _load_split("test_files")

    logger.info("Loaded Train: %d, Val: %d, Test: %d", len(x_train), len(x_val), len(x_test))
    return (x_train, y_train), (x_val, y_val), (x_test, y_test)


def build_augmentation_layer():
    """Moderate geometric data augmentation layer applied only during training."""
    import tensorflow as tf
    from tensorflow.keras import layers

    return tf.keras.Sequential([
        layers.RandomFlip("horizontal", seed=SEED),
        layers.RandomRotation(0.06, seed=SEED),            # ~15 degrees max
        layers.RandomZoom(height_factor=(-0.05, 0.05), seed=SEED),
        layers.RandomTranslation(height_factor=0.04, width_factor=0.04, seed=SEED),
    ], name="data_augmentation")


def build_mobilenetv2_model(num_classes: int):
    """Builds MobileNetV2 model with ImageNet weights and regularized classification head."""
    import tensorflow as tf
    from tensorflow.keras import layers, Model
    from tensorflow.keras.applications import MobileNetV2

    base = MobileNetV2(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False

    aug_layer = build_augmentation_layer()

    inputs = tf.keras.Input(shape=(*IMG_SIZE, 3), name="input_image")
    # Augmentation active only during training
    x = aug_layer(inputs)
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D(name="global_avg_pool")(x)
    x = layers.Dropout(0.3, name="top_dropout_1")(x)
    x = layers.Dense(
        128,
        activation="relu",
        kernel_regularizer=tf.keras.regularizers.l2(1e-4),
        name="dense_128"
    )(x)
    x = layers.Dropout(0.2, name="top_dropout_2")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="predictions")(x)

    model = Model(inputs, outputs, name="AgroSmart_MobileNetV2_SoilClassifier_v2")
    return model, base


def train_model():
    set_seed(SEED)
    import tensorflow as tf

    classes = joblib.load(CLASSES_PATH)
    logger.info("Model classes: %s", classes)

    # 1. Load data
    (x_train, y_train), (x_val, y_val), (x_test, y_test) = load_dataset_from_splits(
        SPLITS_PATH, CLEAN_DIR, classes
    )

    # 2. Compute balanced class weights with boost for Clay
    raw_weights = compute_class_weight("balanced", classes=np.unique(y_train), y=y_train)
    class_weight_dict = {i: float(w) for i, w in enumerate(raw_weights)}

    # Slight boost for Clay (class index 2) to improve recall
    clay_idx = classes.index("Clay")
    class_weight_dict[clay_idx] *= 1.25
    logger.info("Configured class weights: %s", {classes[i]: round(class_weight_dict[i], 4) for i in class_weight_dict})

    # One-hot encode targets
    y_train_cat = tf.keras.utils.to_categorical(y_train, num_classes=len(classes))
    y_val_cat = tf.keras.utils.to_categorical(y_val, num_classes=len(classes))
    y_test_cat = tf.keras.utils.to_categorical(y_test, num_classes=len(classes))

    # 3. Build model
    model, base = build_mobilenetv2_model(len(classes))
    logger.info("Total Model parameters: %d (Trainable: %d)", model.count_params(), np.sum([np.prod(v.shape) for v in model.trainable_weights]))

    checkpoint_cb = tf.keras.callbacks.ModelCheckpoint(
        filepath=str(MODEL_V2_OUT),
        monitor="val_loss",
        save_best_only=True,
        mode="min",
        verbose=1,
    )

    # ── STAGE 1: Train Classification Head (Backbone Frozen) ──────────────────
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks_stage1 = [
        checkpoint_cb,
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True, verbose=1),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2, min_lr=1e-5, verbose=1),
    ]

    logger.info("=" * 70)
    logger.info("STAGE 1: Training Classification Head (Backbone Frozen, up to 15 epochs)")
    logger.info("=" * 70)
    hist1 = model.fit(
        x_train, y_train_cat,
        validation_data=(x_val, y_val_cat),
        epochs=15,
        batch_size=BATCH_SIZE,
        class_weight=class_weight_dict,
        callbacks=callbacks_stage1,
        verbose=1,
    )

    # ── STAGE 2: Fine-Tuning Top 25 Backbone Layers ───────────────────────────
    logger.info("=" * 70)
    logger.info("STAGE 2: Fine-Tuning Top 25 Layers of MobileNetV2 (BatchNorm Frozen)")
    logger.info("=" * 70)
    base.trainable = True

    # Freeze all layers except top 25
    for layer in base.layers[:-25]:
        layer.trainable = False

    # CRITICAL: Keep BatchNormalization layers frozen
    frozen_bn = 0
    for layer in base.layers:
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False
            frozen_bn += 1
    logger.info("Froze %d BatchNormalization layers in MobileNetV2 base", frozen_bn)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=3e-5),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks_stage2 = [
        checkpoint_cb,
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True, verbose=1),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2, min_lr=1e-6, verbose=1),
    ]

    hist2 = model.fit(
        x_train, y_train_cat,
        validation_data=(x_val, y_val_cat),
        epochs=15,
        batch_size=BATCH_SIZE,
        class_weight=class_weight_dict,
        callbacks=callbacks_stage2,
        verbose=1,
    )

    # ── STAGE 3: Final Model Selection & Test Evaluation ──────────────────────
    logger.info("Loading best model checkpoint from %s...", MODEL_V2_OUT)
    best_model = tf.keras.models.load_model(str(MODEL_V2_OUT))

    # Save classes for v2
    joblib.dump(classes, CLASSES_V2_OUT)
    logger.info("Saved v2 classes to %s", CLASSES_V2_OUT)

    logger.info("=" * 70)
    logger.info("STAGE 3: Evaluating Best v2 Model on Clean Test Set (n=71)")
    logger.info("=" * 70)

    preds_prob = best_model.predict(x_test, verbose=0)
    y_pred = np.argmax(preds_prob, axis=1)

    test_loss = float(tf.keras.losses.categorical_crossentropy(y_test_cat, preds_prob).numpy().mean())
    test_acc = float(accuracy_score(y_test, y_pred))
    test_prec_macro = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    test_rec_macro = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    test_f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    test_f1_weighted = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
    cm = confusion_matrix(y_test, y_pred, labels=range(len(classes)))
    report = classification_report(y_test, y_pred, target_names=classes, output_dict=True)

    # Validation evaluation for completeness
    val_preds_prob = best_model.predict(x_val, verbose=0)
    y_val_pred = np.argmax(val_preds_prob, axis=1)
    val_loss = float(tf.keras.losses.categorical_crossentropy(y_val_cat, val_preds_prob).numpy().mean())
    val_acc = float(accuracy_score(y_val, y_val_pred))

    logger.info("Held-Out Test Results:")
    logger.info("  Loss           : %.4f", test_loss)
    logger.info("  Accuracy       : %.4f (%.2f%%)", test_acc, test_acc * 100)
    logger.info("  Macro Precision: %.4f", test_prec_macro)
    logger.info("  Macro Recall   : %.4f", test_rec_macro)
    logger.info("  Macro F1-Score : %.4f", test_f1_macro)
    logger.info("  Weighted F1    : %.4f", test_f1_weighted)
    logger.info("\nClassification Report:\n%s", classification_report(y_test, y_pred, target_names=classes))
    logger.info("\nConfusion Matrix (%s):\n%s", classes, cm)

    # Save comprehensive metrics & epoch logs
    metrics_payload = {
        "metadata": {
            "model_version": "v2",
            "model_path": str(MODEL_V2_OUT.resolve()),
            "classes": classes,
            "img_size": list(IMG_SIZE),
            "batch_size": BATCH_SIZE,
            "seed": SEED,
            "class_weights": {classes[i]: class_weight_dict[i] for i in class_weight_dict},
            "train_samples": len(x_train),
            "val_samples": len(x_val),
            "test_samples": len(x_test),
        },
        "stage1_history": {
            "loss": [float(v) for v in hist1.history["loss"]],
            "accuracy": [float(v) for v in hist1.history["accuracy"]],
            "val_loss": [float(v) for v in hist1.history["val_loss"]],
            "val_accuracy": [float(v) for v in hist1.history["val_accuracy"]],
            "lr": [float(v) for v in hist1.history.get("lr", [1e-3] * len(hist1.history["loss"]))],
        },
        "stage2_history": {
            "loss": [float(v) for v in hist2.history["loss"]],
            "accuracy": [float(v) for v in hist2.history["accuracy"]],
            "val_loss": [float(v) for v in hist2.history["val_loss"]],
            "val_accuracy": [float(v) for v in hist2.history["val_accuracy"]],
            "lr": [float(v) for v in hist2.history.get("lr", [3e-5] * len(hist2.history["loss"]))],
        },
        "validation_evaluation": {
            "loss": val_loss,
            "accuracy": val_acc,
        },
        "test_evaluation": {
            "loss": test_loss,
            "accuracy": test_acc,
            "macro_precision": test_prec_macro,
            "macro_recall": test_rec_macro,
            "macro_f1": test_f1_macro,
            "weighted_f1": test_f1_weighted,
            "confusion_matrix": cm.tolist(),
            "classification_report": report,
        },
        "v1_baseline_comparison": {
            "v1_test_accuracy": 0.8169,
            "v2_test_accuracy": test_acc,
            "accuracy_difference": test_acc - 0.8169,
            "v1_macro_f1": 0.8162,
            "v2_macro_f1": test_f1_macro,
            "macro_f1_difference": test_f1_macro - 0.8162,
            "v1_clay_recall": 0.6667,
            "v2_clay_recall": report["Clay"]["recall"],
            "clay_recall_difference": report["Clay"]["recall"] - 0.6667,
        }
    }

    with open(METRICS_V2_OUT, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)
    logger.info("Saved v2 training metrics and evaluation history to %s", METRICS_V2_OUT)

    return metrics_payload


if __name__ == "__main__":
    train_model()
