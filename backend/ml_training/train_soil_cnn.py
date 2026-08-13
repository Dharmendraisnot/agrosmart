"""
train_soil_cnn.py — Train the CNN soil image classification model.

Architecture: MobileNetV2 (pretrained on ImageNet) + custom classification head.
Chosen for: lightweight inference on Raspberry Pi 5, high accuracy on small datasets
via transfer learning.

Dataset: Soil type image dataset
  Structure expected:
    ml_training/datasets/soil_images/
      Sandy/        ← RGB images of sandy soil
      Clay/         ← RGB images of clay soil
      Loamy/        ← RGB images of loamy soil
      Silty/        ← RGB images of silty soil

  Recommended dataset: search Kaggle for "Soil Type Classification"
  or "Soil Image Dataset". Place images in the class subdirectories above.

Output:
  trained_models/soil_cnn_v1.h5        — saved Keras model
  trained_models/soil_cnn_classes.pkl  — class name list (order matches model output)

Usage:
  python ml_training/train_soil_cnn.py

Notes:
  - Requires TensorFlow. Install: pip install tensorflow opencv-python-headless Pillow
  - Training on CPU is slow; use GPU if available.
  - MobileNetV2 base is frozen for initial training, then fine-tuned (top layers).
  - If the soil_images dataset is absent, the script exits with instructions.
"""
from __future__ import annotations

import sys
import logging
from pathlib import Path

import joblib
import numpy as np

# ── Path setup ────────────────────────────────────────────────────────────────
BACKEND_DIR   = Path(__file__).resolve().parent.parent
IMAGES_DIR    = BACKEND_DIR / "ml_training" / "datasets" / "soil_images"
MODELS_DIR    = BACKEND_DIR / "trained_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_OUT     = MODELS_DIR / "soil_cnn_v1.h5"
CLASSES_OUT   = MODELS_DIR / "soil_cnn_classes.pkl"

# ── Hyperparameters ───────────────────────────────────────────────────────────
IMG_SIZE      = (224, 224)   # MobileNetV2 default input size
BATCH_SIZE    = 32
EPOCHS_FROZEN = 10           # epochs with MobileNetV2 base frozen
EPOCHS_FINETUNE = 5          # epochs with top 20 layers unfrozen
VALIDATION_SPLIT = 0.2
SEED          = 42

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)


def check_dataset() -> list[str]:
    """Verify dataset directory and return sorted class names."""
    if not IMAGES_DIR.exists():
        logger.error(
            "Soil images directory not found: %s\n"
            "Create subdirectories for each soil class:\n"
            "  soil_images/Sandy/   soil_images/Clay/\n"
            "  soil_images/Loamy/   soil_images/Silty/\n"
            "Then place representative RGB images in each.",
            IMAGES_DIR,
        )
        sys.exit(1)

    classes = sorted([d.name for d in IMAGES_DIR.iterdir() if d.is_dir()])
    if len(classes) < 2:
        logger.error("Need at least 2 class subdirectories in %s, found: %s",
                     IMAGES_DIR, classes)
        sys.exit(1)

    total = sum(len(list((IMAGES_DIR / c).glob("*.*"))) for c in classes)
    logger.info("Dataset: %d classes, ~%d images total", len(classes), total)
    for c in classes:
        n = len(list((IMAGES_DIR / c).glob("*.*")))
        logger.info("  %-12s  %d images", c, n)
    return classes


def build_model(num_classes: int):
    """
    Build MobileNetV2 transfer learning model.
    Base is frozen; only the custom head trains in phase 1.
    """
    import tensorflow as tf
    from tensorflow.keras import layers, Model
    from tensorflow.keras.applications import MobileNetV2

    base = MobileNetV2(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False   # freeze pretrained weights

    inputs  = tf.keras.Input(shape=(*IMG_SIZE, 3))
    x = base(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model, base


def get_data_generators(classes: list[str]):
    """Build training and validation ImageDataGenerators."""
    import tensorflow as tf
    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255.0,
        validation_split=VALIDATION_SPLIT,
        rotation_range=20,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
        zoom_range=0.15,
    )

    train_gen = train_datagen.flow_from_directory(
        IMAGES_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="training",
        seed=SEED,
        classes=classes,
    )
    val_gen = train_datagen.flow_from_directory(
        IMAGES_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="validation",
        seed=SEED,
        classes=classes,
    )
    return train_gen, val_gen


def train_and_evaluate(classes: list[str]) -> dict:
    import tensorflow as tf

    model, base = build_model(len(classes))
    logger.info("Model built. Parameters: %d", model.count_params())

    train_gen, val_gen = get_data_generators(classes)

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=5, restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6
        ),
    ]

    # Phase 1 — train head only (base frozen)
    logger.info("Phase 1: Training classification head (%d epochs)…", EPOCHS_FROZEN)
    history1 = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_FROZEN,
        callbacks=callbacks,
        verbose=1,
    )

    # Phase 2 — fine-tune top 20 layers of MobileNetV2
    logger.info("Phase 2: Fine-tuning top 20 base layers (%d epochs)…", EPOCHS_FINETUNE)
    base.trainable = True
    for layer in base.layers[:-20]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    history2 = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_FINETUNE,
        callbacks=callbacks,
        verbose=1,
    )

    # Final validation accuracy
    val_loss, val_acc = model.evaluate(val_gen, verbose=0)

    metrics = {
        "val_accuracy":  round(float(val_acc),  4),
        "val_loss":      round(float(val_loss),  4),
        "n_classes":     len(classes),
        "classes":       classes,
        "img_size":      list(IMG_SIZE),
        "architecture":  "MobileNetV2 + custom head",
    }
    return model, metrics


def main() -> None:
    logger.info("AgroSmart — Soil CNN Model Training (MobileNetV2)")

    try:
        import tensorflow as tf
        logger.info("TensorFlow version: %s", tf.__version__)
    except ImportError:
        logger.error(
            "TensorFlow not installed.\n"
            "Install with: pip install tensorflow opencv-python-headless Pillow"
        )
        sys.exit(1)

    classes = check_dataset()
    model, metrics = train_and_evaluate(classes)

    # Save model and class list
    model.save(str(MODEL_OUT))
    joblib.dump(classes, CLASSES_OUT)

    logger.info("=" * 60)
    logger.info("SOIL CNN MODEL — EVALUATION RESULTS")
    logger.info("=" * 60)
    logger.info("Architecture : %s", metrics["architecture"])
    logger.info("Classes      : %s", metrics["classes"])
    logger.info("Val accuracy : %.4f  (%.1f%%)", metrics["val_accuracy"],
                metrics["val_accuracy"] * 100)
    logger.info("Val loss     : %.4f", metrics["val_loss"])
    logger.info("Model saved  → %s", MODEL_OUT)
    logger.info("Classes saved→ %s", CLASSES_OUT)
    logger.info("Training complete.")


if __name__ == "__main__":
    main()
