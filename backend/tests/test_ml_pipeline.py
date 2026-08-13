"""
test_ml_pipeline.py — Unit tests for ML inference wrappers.

Tests:
  - CropInferencePreprocessor transforms sensor dict to correct shape
  - FertilizerInferencePreprocessor handles unseen labels gracefully
  - predict_crops returns correctly structured list
  - predict_fertilizer returns required keys including model_label
  - generate_irrigation_advice covers all urgency levels
  - _compute_health_score produces scores in valid range
  - recommendation_service handles None moisture gracefully
"""
import pytest
import numpy as np


# ── Preprocessor tests ────────────────────────────────────────────────────────

class TestCropInferencePreprocessor:

    @pytest.fixture(autouse=True)
    def setup(self, app):
        with app.app_context():
            from pathlib import Path
            from app.ml.preprocessor import CropInferencePreprocessor
            scaler_path = Path(app.config["CROP_MODEL_PATH"]).parent / "crop_scaler.pkl"
            if not scaler_path.exists():
                pytest.skip("crop_scaler.pkl not found — run train_crop_model.py first")
            self.preprocessor = CropInferencePreprocessor(scaler_path)

    def test_transform_returns_correct_shape(self):
        sensor = {
            "nitrogen": 40, "phosphorus": 20, "potassium": 180,
            "soil_temperature": 24, "air_humidity": 65, "ph": 6.5, "moisture": 52,
        }
        result = self.preprocessor.transform(sensor)
        assert result.shape == (1, 7)

    def test_transform_handles_none_values(self):
        """None values should be replaced with medians, not raise errors."""
        sensor = {"nitrogen": None, "phosphorus": None, "potassium": None,
                  "ph": None, "moisture": None, "soil_temperature": None, "air_humidity": None}
        result = self.preprocessor.transform(sensor)
        assert result.shape == (1, 7)
        assert not np.any(np.isnan(result))

    def test_transform_handles_partial_keys(self):
        """Partial dict (some keys missing) should use medians for missing."""
        sensor = {"ph": 6.8, "moisture": 45.0}
        result = self.preprocessor.transform(sensor)
        assert result.shape == (1, 7)


class TestFertilizerInferencePreprocessor:

    @pytest.fixture(autouse=True)
    def setup(self, app):
        with app.app_context():
            from pathlib import Path
            from app.ml.preprocessor import FertilizerInferencePreprocessor
            scaler_path   = Path(app.config["FERTILIZER_MODEL_PATH"]).parent / "fertilizer_scaler.pkl"
            encoders_path = Path(app.config["FERTILIZER_MODEL_PATH"]).parent / "fertilizer_encoders.pkl"
            if not scaler_path.exists():
                pytest.skip("fertilizer_scaler.pkl not found — run train_fertilizer_model.py first")
            self.preprocessor = FertilizerInferencePreprocessor(scaler_path, encoders_path)

    def test_transform_returns_correct_shape(self):
        sensor = {
            "air_temperature": 30, "air_humidity": 65, "moisture": 52,
            "nitrogen": 40, "potassium": 180, "phosphorus": 20,
        }
        result = self.preprocessor.transform(sensor, soil_type="Loamy", crop_type="Wheat")
        assert result.shape == (1, 8)

    def test_unseen_soil_type_uses_fallback(self):
        """Unseen soil type label should not raise — falls back to index 0."""
        sensor = {"air_temperature": 30, "air_humidity": 65, "moisture": 52,
                  "nitrogen": 40, "potassium": 180, "phosphorus": 20}
        result = self.preprocessor.transform(sensor, soil_type="Volcanic_Lava", crop_type="Wheat")
        assert result.shape == (1, 8)

    def test_unseen_crop_type_uses_fallback(self):
        sensor = {"air_temperature": 30, "air_humidity": 65, "moisture": 52,
                  "nitrogen": 40, "potassium": 180, "phosphorus": 20}
        result = self.preprocessor.transform(sensor, soil_type="Loamy", crop_type="AlienCrop")
        assert result.shape == (1, 8)


# ── Crop model tests ──────────────────────────────────────────────────────────

class TestCropModel:

    def test_predict_crops_returns_list(self, app):
        with app.app_context():
            from pathlib import Path
            if not Path(app.config["CROP_MODEL_PATH"]).exists():
                pytest.skip("crop model not found")
            from app.ml.crop_model import predict_crops, reload_model
            reload_model()
            sensor = {
                "nitrogen": 82, "phosphorus": 46, "potassium": 43,
                "soil_temperature": 20, "air_humidity": 82, "ph": 6.5, "moisture": 202,
            }
            result = predict_crops(sensor, dict(app.config), top_n=3)
            assert isinstance(result, list)
            assert len(result) == 3

    def test_predict_crops_result_structure(self, app):
        with app.app_context():
            from pathlib import Path
            if not Path(app.config["CROP_MODEL_PATH"]).exists():
                pytest.skip("crop model not found")
            from app.ml.crop_model import predict_crops, reload_model
            reload_model()
            sensor = {"nitrogen": 40, "ph": 6.5, "moisture": 50}
            result = predict_crops(sensor, dict(app.config), top_n=3)
            for item in result:
                assert "crop" in item
                assert "confidence" in item
                assert "rank" in item
                assert 0.0 <= item["confidence"] <= 1.0
                assert item["rank"] in (1, 2, 3)

    def test_predict_crops_ranks_are_ordered(self, app):
        with app.app_context():
            from pathlib import Path
            if not Path(app.config["CROP_MODEL_PATH"]).exists():
                pytest.skip("crop model not found")
            from app.ml.crop_model import predict_crops, reload_model
            reload_model()
            sensor = {"nitrogen": 40, "ph": 6.5, "moisture": 50}
            result = predict_crops(sensor, dict(app.config), top_n=3)
            confidences = [r["confidence"] for r in result]
            assert confidences == sorted(confidences, reverse=True)


# ── Fertilizer model tests ────────────────────────────────────────────────────

class TestFertilizerModel:

    def test_predict_fertilizer_structure(self, app):
        with app.app_context():
            from pathlib import Path
            if not Path(app.config["FERTILIZER_MODEL_PATH"]).exists():
                pytest.skip("fertilizer model not found")
            from app.ml.fertilizer_model import predict_fertilizer, reload_model
            reload_model()
            sensor = {"air_temperature": 30, "air_humidity": 65, "moisture": 52,
                      "nitrogen": 40, "potassium": 180, "phosphorus": 20}
            result = predict_fertilizer(sensor, "Loamy", "wheat", dict(app.config))
            assert "fertilizer"  in result
            assert "advice"      in result
            assert "model_label" in result
            assert "soil_type"   in result
            assert "crop"        in result

    def test_predict_fertilizer_model_label_set(self, app):
        with app.app_context():
            from pathlib import Path
            if not Path(app.config["FERTILIZER_MODEL_PATH"]).exists():
                pytest.skip("fertilizer model not found")
            from app.ml.fertilizer_model import predict_fertilizer, reload_model
            reload_model()
            sensor = {"moisture": 50, "nitrogen": 30, "phosphorus": 15, "potassium": 100}
            result = predict_fertilizer(sensor, "Sandy", "maize", dict(app.config))
            assert result["model_label"] != ""
            assert result["model_label"] is not None


# ── Irrigation rule engine tests ──────────────────────────────────────────────

class TestIrrigationAdvice:

    def setup_method(self):
        from app.services.recommendation_service import generate_irrigation_advice
        self.gen = generate_irrigation_advice

    def test_critical_moisture(self):
        result = self.gen({"moisture": 15.0}, soil_type="Sandy", top_crop="rice")
        assert result["urgency"] == "critical"
        assert "immediately" in result["action"].lower()

    def test_high_urgency(self):
        result = self.gen({"moisture": 30.0}, soil_type="Loamy", top_crop="wheat")
        assert result["urgency"] in ("critical", "high")

    def test_adequate_moisture(self):
        result = self.gen({"moisture": 55.0}, soil_type="Loamy", top_crop="wheat")
        assert result["urgency"] == "medium"

    def test_no_irrigation_needed(self):
        result = self.gen({"moisture": 70.0}, soil_type="Clay", top_crop="wheat")
        assert result["urgency"] in ("low", "none")

    def test_oversaturated(self):
        result = self.gen({"moisture": 85.0}, soil_type="Clay")
        assert result["urgency"] == "none"
        assert "saturated" in result["action"].lower()

    def test_none_moisture_returns_unknown(self):
        result = self.gen({"moisture": None})
        assert result["urgency"] == "unknown"
        assert result["raw_moisture"] is None

    def test_temperature_note_high_temp(self):
        result = self.gen({"moisture": 55.0, "air_temperature": 40.0})
        assert result["temperature_note"] is not None
        assert "temperature" in result["temperature_note"].lower()

    def test_temperature_note_normal_temp(self):
        result = self.gen({"moisture": 55.0, "air_temperature": 25.0})
        assert result["temperature_note"] is None

    def test_result_has_all_required_keys(self):
        result = self.gen({"moisture": 50.0})
        required = {"action", "urgency", "frequency", "estimated_water",
                    "effective_moisture", "raw_moisture", "temperature_note", "reasoning"}
        assert required.issubset(set(result.keys()))

    def test_clay_soil_modifier_raises_effective_moisture(self):
        loamy = self.gen({"moisture": 35.0}, soil_type="Loamy")
        clay  = self.gen({"moisture": 35.0}, soil_type="Clay")
        assert clay["effective_moisture"] > loamy["effective_moisture"]

    def test_sandy_soil_modifier_lowers_effective_moisture(self):
        loamy = self.gen({"moisture": 50.0}, soil_type="Loamy")
        sandy = self.gen({"moisture": 50.0}, soil_type="Sandy")
        assert sandy["effective_moisture"] < loamy["effective_moisture"]


# ── Health score tests ────────────────────────────────────────────────────────

class TestHealthScore:

    def setup_method(self):
        from app.services.analysis_service import _compute_health_score
        self.compute = _compute_health_score

    def test_perfect_conditions_score_high(self):
        sensor = {"ph": 6.8, "moisture": 55.0, "soil_temperature": 25.0,
                  "nitrogen": 50.0, "phosphorus": 30.0, "potassium": 180.0}
        score, label = self.compute(sensor, "Loamy")
        assert score >= 70
        assert label == "Good"

    def test_poor_conditions_score_low(self):
        sensor = {"ph": 3.5, "moisture": 5.0, "soil_temperature": 55.0,
                  "nitrogen": 1.0, "phosphorus": 1.0, "potassium": 10.0}
        score, label = self.compute(sensor, "Sandy")
        assert score < 45
        assert label == "Poor"

    def test_score_in_valid_range(self):
        sensor = {"ph": 6.5, "moisture": 50.0, "soil_temperature": 24.0,
                  "nitrogen": 40.0, "phosphorus": 20.0, "potassium": 180.0}
        score, _ = self.compute(sensor, "Loamy")
        assert 0 <= score <= 100

    def test_all_none_values_gives_zero(self):
        sensor = {}
        score, label = self.compute(sensor, None)
        assert score == 0.0
        assert label == "Poor"

    def test_label_matches_score(self):
        for ph, expected_label in [(6.5, "Good"), (5.2, "Fair")]:
            sensor = {"ph": ph, "moisture": 50.0, "soil_temperature": 24.0,
                      "nitrogen": 40.0, "phosphorus": 20.0, "potassium": 180.0}
            score, label = self.compute(sensor, "Loamy")
            if score >= 70:
                assert label == "Good"
            elif score >= 45:
                assert label == "Fair"
            else:
                assert label == "Poor"
