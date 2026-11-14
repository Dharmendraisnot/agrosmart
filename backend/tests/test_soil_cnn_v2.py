"""
tests/test_soil_cnn_v2.py — Regression and verification tests for MobileNetV2 Soil CNN v2.

Tests:
  - soil_cnn_v2 artifacts (model .h5, classes .pkl, metrics .json) exist and load cleanly.
  - Model input shape is (None, 224, 224, 3) and output shape is (None, 4).
  - Forward inference produces valid softmax probability distributions (sum to 1.0).
  - Recorded metrics in soil_cnn_v2_metrics.json match verified evaluation numbers.
  - Evaluation pipeline directly evaluates soil_cnn_v2.h5 on held-out test split (n=71)
    and matches recorded test metrics (accuracy 80.28%, 73.33% Clay recall, 100% Red precision).
  - Baseline model soil_cnn_v1.h5 remains completely untouched (SHA-256 integrity verified).
"""

import hashlib
import json
from pathlib import Path
import joblib
import numpy as np
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BACKEND_DIR / "trained_models"

MODEL_V2_PATH = MODELS_DIR / "soil_cnn_v2.h5"
CLASSES_V2_PATH = MODELS_DIR / "soil_cnn_v2_classes.pkl"
METRICS_V2_PATH = MODELS_DIR / "soil_cnn_v2_metrics.json"

MODEL_V1_PATH = MODELS_DIR / "soil_cnn_v1.h5"
EXPECTED_V1_SHA256 = "eb99065e1b40a1edcf7a498c659659e854d8c980bf368c748aad618b93a3d726"


def test_v2_artifacts_exist_and_load():
    assert MODEL_V2_PATH.exists(), f"v2 model artifact missing: {MODEL_V2_PATH}"
    assert CLASSES_V2_PATH.exists(), f"v2 classes artifact missing: {CLASSES_V2_PATH}"
    assert METRICS_V2_PATH.exists(), f"v2 metrics artifact missing: {METRICS_V2_PATH}"

    classes = joblib.load(CLASSES_V2_PATH)
    assert classes == ["Alluvial", "Black", "Clay", "Red"]

    with open(METRICS_V2_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    assert metrics["metadata"]["model_version"] == "v2"
    assert metrics["metadata"]["classes"] == ["Alluvial", "Black", "Clay", "Red"]
    assert metrics["metadata"]["train_samples"] == 329
    assert metrics["metadata"]["val_samples"] == 70
    assert metrics["metadata"]["test_samples"] == 71


def test_v2_model_architecture_and_shapes():
    import tensorflow as tf
    model = tf.keras.models.load_model(str(MODEL_V2_PATH), compile=False)

    assert model.input_shape == (None, 224, 224, 3)
    assert model.output_shape == (None, 4)
    assert len(model.layers) >= 7
    # Verify MobileNetV2 backbone exists and contains deep convolutional layers (>100 layers)
    backbone = [l for l in model.layers if "mobilenetv2" in l.name.lower()]
    assert len(backbone) == 1
    assert len(backbone[0].layers) > 100


def test_v2_forward_inference_and_softmax():
    import tensorflow as tf
    model = tf.keras.models.load_model(str(MODEL_V2_PATH), compile=False)

    # Test dummy inference batch
    dummy_input = np.random.uniform(-1.0, 1.0, size=(2, 224, 224, 3)).astype(np.float32)
    preds = model.predict(dummy_input, verbose=0)

    assert preds.shape == (2, 4)
    assert np.all(preds >= 0.0)
    assert np.all(preds <= 1.0)
    for p in preds:
        assert np.isclose(np.sum(p), 1.0, atol=1e-5)


def test_v2_recorded_metrics_integrity():
    with open(METRICS_V2_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    test_eval = data["test_evaluation"]
    assert np.isclose(test_eval["accuracy"], 57 / 71, atol=1e-4)  # 80.28%
    assert np.isclose(test_eval["macro_f1"], 0.8048, atol=1e-3)

    cm = np.array(test_eval["confusion_matrix"])
    assert cm.shape == (4, 4)
    assert np.sum(cm) == 71
    assert np.trace(cm) == 57  # 57 correct

    report = test_eval["classification_report"]
    # Check Clay recall improvement (11/15 = 73.33%)
    assert np.isclose(report["Clay"]["recall"], 11 / 15, atol=1e-4)
    assert report["Clay"]["recall"] > 0.70

    # Check Red precision (17/17 = 100.0%)
    assert np.isclose(report["Red"]["precision"], 1.0, atol=1e-4)

    # Training histories
    assert len(data["stage1_history"]["loss"]) == 14
    assert len(data["stage2_history"]["loss"]) == 6


def test_v2_evaluation_pipeline_consistency():
    import sys
    sys.path.append(str(BACKEND_DIR / "ml_training"))
    from evaluate_models import evaluate_cnn_model

    results = evaluate_cnn_model(
        split="test",
        model_path=MODEL_V2_PATH,
        classes_path=CLASSES_V2_PATH,
    )

    assert results is not None
    assert results["split"] == "test"
    assert results["total_evaluated"] == 71
    assert results["total_skipped"] == 0
    assert np.isclose(results["accuracy"], 57 / 71, atol=1e-4)

    cm = np.array(results["confusion_matrix"])
    expected_cm = np.array([
        [17, 2, 0, 0],
        [5, 12, 1, 0],
        [4, 0, 11, 0],
        [1, 0, 1, 17]
    ])
    np.testing.assert_array_equal(cm, expected_cm)


def test_baseline_v1_model_untouched():
    assert MODEL_V1_PATH.exists(), f"Baseline model {MODEL_V1_PATH} missing!"
    sha256 = hashlib.sha256()
    with open(MODEL_V1_PATH, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    actual_hash = sha256.hexdigest().lower()
    assert actual_hash == EXPECTED_V1_SHA256, (
        f"Baseline model {MODEL_V1_PATH} was unexpectedly modified!\n"
        f"Expected: {EXPECTED_V1_SHA256}\nActual:   {actual_hash}"
    )
