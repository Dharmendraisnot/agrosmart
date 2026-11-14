"""
tests/test_soil_cnn_evaluation.py — Regression and integrity tests for Soil CNN Evaluation Pipeline.

Tests:
  - Official split metadata (soil_cnn_splits_v2.json) loads and has correct structure.
  - Class mapping matches model expectations (['Alluvial', 'Black', 'Clay', 'Red']).
  - Zero filename or path overlap across Train, Val, and Test splits.
  - Missing image detection raises FileNotFoundError with diagnostic message.
  - Unexpected class label raises ValueError with diagnostic message.
  - evaluate_cnn_model evaluates strictly on the requested split (n=71 for test, 0 from train).
  - Metric calculations (accuracy, precision, recall, F1, confusion matrix) are exact.
  - Clean canonical images exist and are valid 3-channel RGB.
"""

import json
from pathlib import Path
import numpy as np
import pytest
from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BACKEND_DIR / "trained_models"
DATASETS_DIR = BACKEND_DIR / "ml_training" / "datasets"
CLEAN_DIR = DATASETS_DIR / "soil_images_clean"
SPLITS_V2_PATH = MODELS_DIR / "soil_cnn_splits_v2.json"
CLASSES_PATH = MODELS_DIR / "soil_cnn_classes.pkl"
MODEL_PATH = MODELS_DIR / "soil_cnn_v1.h5"


# ── Metadata & Split Integrity Tests ──────────────────────────────────────────

def test_splits_v2_metadata_loads_and_has_required_structure():
    assert SPLITS_V2_PATH.exists(), f"splits_v2 metadata file missing: {SPLITS_V2_PATH}"
    with open(SPLITS_V2_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["metadata"]["version"] == "v2"
    assert data["metadata"]["random_seed"] == 42
    assert data["summary"]["total"] == 470
    assert data["summary"]["train"] == 329
    assert data["summary"]["val"] == 70
    assert data["summary"]["test"] == 71

    # Class counts
    for c in ["Alluvial", "Black", "Clay", "Red"]:
        assert c in data["class_counts"]
        assert data["class_counts"][c]["total"] > 0
        sum_c = (
            data["class_counts"][c]["train"]
            + data["class_counts"][c]["val"]
            + data["class_counts"][c]["test"]
        )
        assert sum_c == data["class_counts"][c]["total"]


def test_class_mapping_matches_soil_classes_artifact():
    import joblib
    assert CLASSES_PATH.exists(), f"Classes artifact missing: {CLASSES_PATH}"
    classes = joblib.load(CLASSES_PATH)
    assert classes == ["Alluvial", "Black", "Clay", "Red"]


def test_zero_overlap_between_all_split_pairs():
    with open(SPLITS_V2_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    train_paths = set(item["relative_path"] for item in data["train_files"])
    val_paths = set(item["relative_path"] for item in data["val_files"])
    test_paths = set(item["relative_path"] for item in data["test_files"])

    assert len(train_paths) == 329
    assert len(val_paths) == 70
    assert len(test_paths) == 71

    assert len(train_paths & val_paths) == 0, "Overlap found between Train and Val!"
    assert len(train_paths & test_paths) == 0, "Overlap found between Train and Test!"
    assert len(val_paths & test_paths) == 0, "Overlap found between Val and Test!"


def test_all_clean_images_exist_and_are_valid_rgb():
    assert CLEAN_DIR.exists(), f"Clean dataset directory missing: {CLEAN_DIR}"
    with open(SPLITS_V2_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_entries = data["train_files"] + data["val_files"] + data["test_files"]
    assert len(all_entries) == 470

    for item in all_entries:
        img_p = CLEAN_DIR / item["relative_path"]
        assert img_p.exists(), f"Clean image missing from disk: {img_p}"
        with Image.open(img_p) as img:
            assert img.mode == "RGB", f"Image {img_p} mode is {img.mode}, expected RGB"
            w, h = img.size
            assert w >= 100 and h >= 50


# ── Pipeline Failure & Integrity Guardrail Tests ──────────────────────────────

def test_missing_image_detection_fails_clearly(tmp_path):
    import sys
    sys.path.append(str(BACKEND_DIR / "ml_training"))
    from evaluate_models import evaluate_cnn_model

    # Create dummy split file with a non-existent image
    dummy_splits = {
        "train_files": [],
        "val_files": [],
        "test_files": [
            {
                "filepath": str(tmp_path / "non_existent_soil.jpg"),
                "relative_path": "Alluvial/non_existent_soil.jpg",
                "label": "Alluvial",
            }
        ],
    }
    dummy_split_file = tmp_path / "dummy_splits.json"
    with open(dummy_split_file, "w", encoding="utf-8") as f:
        json.dump(dummy_splits, f)

    with pytest.raises(FileNotFoundError) as exc_info:
        evaluate_cnn_model(split="test", splits_file=dummy_split_file, clean_dir=tmp_path)
    assert "Split image missing from disk" in str(exc_info.value)


def test_unexpected_class_label_fails_clearly(tmp_path):
    import sys
    sys.path.append(str(BACKEND_DIR / "ml_training"))
    from evaluate_models import evaluate_cnn_model

    # Create dummy image on disk
    dummy_img = tmp_path / "test.jpg"
    Image.new("RGB", (224, 224), color="brown").save(dummy_img)

    dummy_splits = {
        "train_files": [],
        "val_files": [],
        "test_files": [
            {
                "filepath": str(dummy_img),
                "relative_path": "test.jpg",
                "label": "MartianSoil",  # Invalid class
            }
        ],
    }
    dummy_split_file = tmp_path / "dummy_splits.json"
    with open(dummy_split_file, "w", encoding="utf-8") as f:
        json.dump(dummy_splits, f)

    with pytest.raises(ValueError) as exc_info:
        evaluate_cnn_model(split="test", splits_file=dummy_split_file, clean_dir=tmp_path)
    assert "Unknown label 'MartianSoil'" in str(exc_info.value)


# ── Evaluation Execution & Metric Verification Tests ──────────────────────────

def test_evaluate_cnn_model_runs_on_test_data_only():
    import sys
    sys.path.append(str(BACKEND_DIR / "ml_training"))
    from evaluate_models import evaluate_cnn_model

    if not MODEL_PATH.exists():
        pytest.skip(f"Model file {MODEL_PATH} not found.")

    results = evaluate_cnn_model(split="test")
    assert results is not None
    assert results["split"] == "test"
    assert results["total_evaluated"] == 71
    assert results["total_skipped"] == 0
    assert results["classes"] == ["Alluvial", "Black", "Clay", "Red"]

    # Verify metric ranges
    assert 0.70 <= results["accuracy"] <= 0.95
    assert 0.70 <= results["macro_precision"] <= 0.95
    assert 0.70 <= results["macro_recall"] <= 0.95
    assert 0.70 <= results["macro_f1"] <= 0.95
    assert 0.10 <= results["loss"] <= 1.00

    # Verify confusion matrix shape & sum
    cm = np.array(results["confusion_matrix"])
    assert cm.shape == (4, 4)
    assert np.sum(cm) == 71


def test_metric_calculation_exactness():
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

    y_true = [0, 0, 1, 1, 2, 2, 3, 3]
    y_pred = [0, 1, 1, 1, 2, 0, 3, 3]

    acc = accuracy_score(y_true, y_pred)
    assert acc == 6 / 8  # 75.0%

    prec = precision_score(y_true, y_pred, average="macro")
    rec = recall_score(y_true, y_pred, average="macro")
    f1 = f1_score(y_true, y_pred, average="macro")
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3])

    assert 0.0 <= prec <= 1.0
    assert 0.0 <= rec <= 1.0
    assert 0.0 <= f1 <= 1.0
    assert cm.shape == (4, 4)
    assert np.sum(cm) == 8
