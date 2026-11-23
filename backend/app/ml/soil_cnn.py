"""
ml/soil_cnn.py — CNN soil image classification inference wrapper with thread-safe warmup.

Loads soil_cnn_v1.h5 (MobileNetV2 transfer learning model) and classifies
a preprocessed image array into one of the soil type classes.

Features:
  - Thread-safe warmup_model() to eliminate first-request cold-start latency.
  - Background initialization at application startup.
  - Concurrent request protection: requests arriving during warmup safely wait
    for model readiness rather than duplicating model deserialization.
  - Graceful degradation: if TensorFlow or the model file is unavailable,
    returns "model_unavailable" without crashing the application.

Usage:
    from app.ml.soil_cnn import predict_soil_type, warmup_model
    # Background startup warmup:
    warmup_model(config, async_mode=True)
    # Inference:
    result = predict_soil_type(image_array, config)
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

_model = None
_classes = None
_tf_available = None   # None = not yet checked

# Concurrency & Warmup synchronization primitives
_lock = threading.RLock()
_ready_event = threading.Event()
_is_warming_up = False
_warmup_error: str | None = None
_warmup_thread: threading.Thread | None = None


def _check_tf() -> bool:
    global _tf_available
    if _tf_available is None:
        with _lock:
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
    Must be called under _lock or inside _execute_warmup.
    """
    global _model, _classes, _warmup_error

    if not _check_tf():
        _warmup_error = "TensorFlow not installed"
        return False

    import joblib
    import tensorflow as tf

    model_path = Path(config.get("SOIL_CNN_MODEL_PATH", "trained_models/soil_cnn_v1.h5"))
    classes_path = model_path.parent / "soil_cnn_classes.pkl"

    if not model_path.exists():
        _warmup_error = f"CNN model not found at {model_path}"
        logger.warning(
            "CNN model not found at %s. "
            "Run ml_training/train_soil_cnn.py once soil images are available. "
            "Soil type classification will be skipped until then.",
            model_path,
        )
        return False

    try:
        _model = tf.keras.models.load_model(str(model_path))
        _classes = (
            joblib.load(classes_path)
            if classes_path.exists()
            else ["Alluvial", "Black", "Clay", "Red"]
        )
        _warmup_error = None
        logger.info("CNN soil model loaded from %s  classes=%s", model_path, _classes)
        return True
    except Exception as exc:
        _model = None
        _classes = None
        _warmup_error = str(exc)
        logger.error("Failed to load CNN model from %s: %s", model_path, exc, exc_info=True)
        return False


def _execute_warmup(config: dict) -> bool:
    """
    Internal warmup routine: loads model and runs a dummy forward pass
    to compile/trace execution graphs on CPU.
    """
    global _is_warming_up, _warmup_error
    try:
        with _lock:
            if _model is not None:
                _ready_event.set()
                _is_warming_up = False
                return True
            success = _load(config)
            if not success or _model is None:
                _ready_event.set()
                _is_warming_up = False
                return False

        # Run dummy forward pass to compile graph outside lock
        dummy = np.zeros((1, 224, 224, 3), dtype=np.float32)
        _model.predict(dummy, verbose=0)
        logger.info("CNN soil model warmup and inference graph compilation completed.")
        return True
    except Exception as exc:
        logger.error("CNN soil model warmup failed: %s", exc, exc_info=True)
        _warmup_error = str(exc)
        return False
    finally:
        _is_warming_up = False
        _ready_event.set()


def warmup_model(config: dict, async_mode: bool = True, timeout: float = 180.0) -> bool:
    """
    Preload TensorFlow, load MobileNetV2, and trace the inference graph.

    Args:
        config: Flask app.config dictionary containing SOIL_CNN_MODEL_PATH.
        async_mode: If True (default), runs in a background daemon thread.
                    If False, blocks until warmup finishes.
        timeout: Maximum seconds to wait when async_mode=False.

    Returns:
        True if model is ready (or async thread successfully started), False otherwise.
    """
    global _is_warming_up, _warmup_thread

    if _model is not None:
        return True

    with _lock:
        if _model is not None:
            return True
        if _is_warming_up:
            if not async_mode:
                _ready_event.wait(timeout=timeout)
                return _model is not None
            return True

        _is_warming_up = True
        _ready_event.clear()

        if async_mode:
            _warmup_thread = threading.Thread(
                target=_execute_warmup,
                args=(config,),
                name="CNN-Warmup-Thread",
                daemon=True,
            )
            _warmup_thread.start()
            logger.info("Background CNN warmup thread started.")
            return True

    # Synchronous execution
    return _execute_warmup(config)


def is_model_ready() -> bool:
    """Return True if the CNN model is loaded and ready for inference."""
    return _model is not None


def is_warming_up() -> bool:
    """Return True if background warmup is currently in progress."""
    return _is_warming_up


def predict_soil_type(image_array: np.ndarray, config: dict, wait_timeout: float = 180.0) -> dict:
    """
    Classify a preprocessed 224×224×3 float32 image array.

    Args:
        image_array: numpy array, shape (224, 224, 3), values in [-1, 1]
        config:      Flask app.config dict
        wait_timeout: Max seconds to wait if background warmup is in progress.

    Returns:
        {
          "soil_type":   "Loamy",
          "confidence":  0.87,
          "all_classes": [{"class": "Loamy", "confidence": 0.87}, ...],
          "status":      "ok"  |  "model_unavailable"
        }
    """
    global _model, _classes

    # If background warmup is actively running, safely wait for it to finish
    if _is_warming_up:
        logger.info("CNN inference waiting for background warmup to finish...")
        ready = _ready_event.wait(timeout=wait_timeout)
        if not ready:
            logger.warning("Timed out waiting %ss for CNN warmup to complete.", wait_timeout)
            return {
                "soil_type":   None,
                "confidence":  None,
                "all_classes": [],
                "status":      "model_unavailable",
                "error":       "Warmup timed out",
            }

    # If model is not loaded (e.g. warmup was not initiated or async failed),
    # load under lock to ensure thread safety
    if _model is None:
        with _lock:
            if _model is None:
                loaded = _load(config)
                if not loaded or _model is None:
                    return {
                        "soil_type":   None,
                        "confidence":  None,
                        "all_classes": [],
                        "status":      "model_unavailable",
                        "error":       _warmup_error,
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
    global _model, _classes, _is_warming_up, _warmup_error, _warmup_thread
    with _lock:
        _model = _classes = None
        _is_warming_up = False
        _ready_event.clear()
        _warmup_error = None
        _warmup_thread = None
    logger.info("CNN model cache cleared — will reload on next call")
