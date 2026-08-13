"""
ml/soil_cnn.py — CNN soil image classification inference wrapper.

Loads soil_cnn_v1.h5 (MobileNetV2 transfer learning model) and classifies
a preprocessed image array into one of the soil type classes.

This wrapper gracefully handles the case where:
  - TensorFlow is not installed (development without GPU).
  - The model file does not yet exist (CNN training deferred to Phase 5).
In both cases it returns a "model_unavailable" result so the rest of the
analysis pipeline can still run using sensor-only data.

Usage (called from image_service.py, not directly from routes):
    from app.ml.soil_cnn import predict_soil_type
    result = predict_soil_type(image_array, config)
    # {"soil_type": "Loamy", "confidence": 0.87, "all_classes": [...]}
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

_model   = None
_classes = None
_tf_available = None   # None = not yet checked


def _check_tf() -> bool:
    global _tf_available
    if _tf_available is None:
        try:
            import tensorflow  # noqa: F401
            _tf_available = True
        except ImportError:
            _tf_available = False
            logger.warning(
                "TensorFlow not installed — CNN soil classification unavailable. "
                "Install with: pip install tensorflow opencv-python-headless Pillow"
            )
    return _tf_available


def _load(config: dict) -> bool:
    """
    Load model + class list. Returns True if successful, False otherwise.
    Failure is non-fatal — the rest of the pipeline continues.
    """
    global _model, _classes

    if not _check_tf():
        return False

    import joblib
    import tensorflow as tf

    model_path   = Path(config["SOIL_CNN_MODEL_PATH"])
    classes_path = model_path.parent / "soil_cnn_classes.pkl"

    if not model_path.exists():
        logger.warning(
            "CNN model not found at %s. "
            "Run ml_training/train_soil_cnn.py once soil images are available. "
            "Soil type classification will be skipped until then.",
            model_path,
        )
        return False

    _model   = tf.keras.models.load_model(str(model_path))
    _classes = joblib.load(classes_path) if classes_path.exists() else ["Sandy", "Clay", "Loamy", "Silty"]
    logger.info("CNN soil model loaded from %s  classes=%s", model_path, _classes)
    return True


def predict_soil_type(image_array: np.ndarray, config: dict) -> dict:
    """
    Classify a preprocessed 224×224×3 float32 image array.

    Args:
        image_array: numpy array, shape (224, 224, 3), values in [0, 1]
        config:      Flask app.config dict

    Returns:
        {
          "soil_type":   "Loamy",
          "confidence":  0.87,
          "all_classes": [{"class": "Loamy", "confidence": 0.87}, ...],
          "status":      "ok"  |  "model_unavailable"
        }
    """
    global _model, _classes

    if _model is None:
        loaded = _load(config)
        if not loaded:
            return {
                "soil_type":   None,
                "confidence":  None,
                "all_classes": [],
                "status":      "model_unavailable",
            }

    # Add batch dimension: (1, 224, 224, 3)
    x = np.expand_dims(image_array.astype(np.float32), axis=0)
    probas = _model.predict(x, verbose=0)[0]

    top_idx    = int(np.argmax(probas))
    soil_type  = _classes[top_idx]
    confidence = float(probas[top_idx])

    all_classes = [
        {"class": _classes[i], "confidence": round(float(probas[i]), 4)}
        for i in range(len(_classes))
    ]
    # Sort by confidence descending
    all_classes.sort(key=lambda d: d["confidence"], reverse=True)

    result = {
        "soil_type":   soil_type,
        "confidence":  round(confidence, 4),
        "all_classes": all_classes,
        "status":      "ok",
    }
    logger.debug("CNN prediction: %s", result)
    return result


def reload_model() -> None:
    """Force model reload on the next predict call."""
    global _model, _classes
    _model = _classes = None
    logger.info("CNN model cache cleared — will reload on next call")
