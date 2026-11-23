"""
tests/test_hybrid_fertilizer_routing.py — Integration and regression tests for Phase 2
Hybrid Fertilizer Recommendation System.

Covers:
  - Preserving Decision Tree ML routing for field crops (10 canonical + synonyms)
  - Routing 12 horticultural / orchard crops to the ICAR/SAU knowledge base
  - Validating status="horticultural_guideline" and all structured output keys
  - Dynamic orchard tree age scaling via parameter and sensor dict
  - Strict guard against unverified or missing data (withheld advice)
  - Unsupported fallback for unrecognized crops and empty crops
  - Alluvial soil texture confirmation guard
"""
import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def check_model_present(app):
    with app.app_context():
        if not Path(app.config["FERTILIZER_MODEL_PATH"]).exists():
            pytest.skip("fertilizer model file not found")
        from app.ml.fertilizer_model import reload_model
        reload_model()


class TestDecisionTreeFieldCropRouting:
    """Verify ML Decision Tree pipeline is preserved for supported field crops."""

    SUPPORTED_CROPS = [
        # Direct matches
        "rice", "maize", "cotton", "kidneybeans", "wheat", "barley",
        "millets", "sugarcane", "tobacco", "ground nuts",
        # Leguminous pulses
        "chickpea", "lentil", "blackgram", "mungbean", "mothbeans", "pigeonpeas",
    ]

    @pytest.mark.parametrize("crop", SUPPORTED_CROPS)
    def test_field_crop_routes_to_ml_model(self, app, crop):
        with app.app_context():
            from app.ml.fertilizer_model import predict_fertilizer, _FERTILIZER_ADVICE
            sensor = {
                "air_temperature": 28, "air_humidity": 65, "moisture": 50,
                "nitrogen": 45, "potassium": 160, "phosphorus": 25,
            }
            result = predict_fertilizer(sensor, "Loamy", crop, dict(app.config))
            assert result["status"] == "supported"
            assert result["crop"] == crop
            assert result["fertilizer"] in _FERTILIZER_ADVICE
            assert result["mapped_crop_category"] is not None
            assert result["mapped_crop_category"] != "Horticultural Knowledge Base"
            assert "prototype" in result["model_label"] or "final" in result["model_label"]


class TestHorticulturalKnowledgeRouting:
    """Verify the 12 non-field crops route to the horticultural knowledge base."""

    HORT_CROPS = [
        "apple", "banana", "coconut", "coffee", "grapes", "jute",
        "mango", "muskmelon", "orange", "papaya", "pomegranate", "watermelon",
    ]

    REQUIRED_STRUCTURED_KEYS = [
        "fertilizer", "advice", "model_label", "soil_type", "crop",
        "mapped_crop_category", "status", "headline", "dosage_summary",
        "dosage_unit", "application_method", "timing_and_splits",
        "organic_manure", "micronutrients", "special_cautions",
        "authority_sources", "verified", "missing_or_unverified_fields",
        "horticulture_details",
    ]

    @pytest.mark.parametrize("crop", HORT_CROPS)
    def test_horticultural_crop_returns_structured_guidelines(self, app, crop):
        with app.app_context():
            from app.ml.fertilizer_model import predict_fertilizer
            sensor = {
                "air_temperature": 29, "air_humidity": 60, "moisture": 48,
                "nitrogen": 50, "potassium": 150, "phosphorus": 30,
            }
            result = predict_fertilizer(sensor, "Loamy", crop, dict(app.config))

            assert result["status"] == "horticultural_guideline"
            assert result["crop"] == crop
            assert result["mapped_crop_category"] == "Horticultural Knowledge Base"
            assert result["model_label"] == "icar_extension_v1.0"
            assert result["verified"] is True

            for key in self.REQUIRED_STRUCTURED_KEYS:
                assert key in result, f"Missing key '{key}' in result for {crop}"

            assert len(result["advice"]) > 10
            assert len(result["application_method"]) > 10
            assert len(result["authority_sources"]) >= 1
            assert len(result["timing_and_splits"]) >= 1

    def test_horticultural_aliases_route_correctly(self, app):
        with app.app_context():
            from app.ml.fertilizer_model import predict_fertilizer
            sensor = {"air_temperature": 28, "air_humidity": 60, "moisture": 50}

            # Citrus aliases -> Orange
            for alias in ["citrus", "mandarin", "sweet orange"]:
                res = predict_fertilizer(sensor, "Loamy", alias, dict(app.config))
                assert res["status"] == "horticultural_guideline"
                assert "Orange" in res["fertilizer"] or "Citrus" in res["fertilizer"]

            # Cucurbit alias
            res_melon = predict_fertilizer(sensor, "Loamy", "musk melon", dict(app.config))
            assert res_melon["status"] == "horticultural_guideline"
            assert "Muskmelon" in res_melon["fertilizer"]

            # Hindi vernacular alias
            res_aam = predict_fertilizer(sensor, "Loamy", "aam", dict(app.config))
            assert res_aam["status"] == "horticultural_guideline"
            assert "Mango" in res_aam["fertilizer"]


class TestTreeAgeScaling:
    """Verify age-aware dose scaling for orchard fruit trees."""

    def test_mango_explicit_age_parameter(self, app):
        with app.app_context():
            from app.ml.fertilizer_model import predict_fertilizer
            sensor = {"air_temperature": 28, "air_humidity": 60, "moisture": 50}

            # Year 1
            res_yr1 = predict_fertilizer(sensor, "Loamy", "mango", dict(app.config), tree_age_years=1)
            assert "Year 1 Young Tree" in res_yr1["dosage_summary"]
            assert "100g N" in res_yr1["dosage_summary"]

            # Year 4
            res_yr4 = predict_fertilizer(sensor, "Loamy", "mango", dict(app.config), tree_age_years=4)
            assert "Tree Age 4" in res_yr4["dosage_summary"]
            assert "400g N" in res_yr4["dosage_summary"]

            # Year 12
            res_yr12 = predict_fertilizer(sensor, "Loamy", "mango", dict(app.config), tree_age_years=12)
            assert "Mature Tree" in res_yr12["dosage_summary"]
            assert "1000g N" in res_yr12["dosage_summary"]

    def test_tree_age_from_sensor_dict(self, app):
        with app.app_context():
            from app.ml.fertilizer_model import predict_fertilizer
            sensor = {"tree_age": 3, "air_temperature": 28, "moisture": 50}
            res = predict_fertilizer(sensor, "Loamy", "apple", dict(app.config))
            assert "Tree Age 3" in res["dosage_summary"]


class TestSafetyGuardsAndEdgeCases:
    """Verify fallback handling for unverified data, unknown crops, and Alluvial soils."""

    def test_unverified_horticultural_data_withheld(self, app, monkeypatch):
        """If a crop profile is marked verified=False, recommendations must be withheld."""
        with app.app_context():
            import app.ml.fertilizer_model as fert_mod
            from app.ml.fertilizer_model import predict_fertilizer

            # Mock format_horticultural_advisory to simulate unverified data
            def mock_advisory(crop_name, tree_age_years=None):
                return {
                    "common_name": "TestCrop",
                    "verified": False,
                    "dosage_summary": "Unverified experimental data",
                }

            monkeypatch.setattr(fert_mod, "format_horticultural_advisory", mock_advisory)

            sensor = {"air_temperature": 28, "moisture": 50}
            result = predict_fertilizer(sensor, "Loamy", "mango", dict(app.config))
            assert result["status"] == "unsupported"
            assert result["fertilizer"] == "Reliable recommendation unavailable"
            assert "unverified or incomplete" in result["advice"]

    def test_unknown_arbitrary_crop_fallback(self, app):
        """Crops unrecognized by both ML and Knowledge Base must return unavailable."""
        with app.app_context():
            from app.ml.fertilizer_model import predict_fertilizer
            sensor = {"air_temperature": 28, "moisture": 50}

            for alien in ["AlienFruit", "DragonFruit", "NonExistentCrop99"]:
                result = predict_fertilizer(sensor, "Loamy", alien, dict(app.config))
                assert result["status"] == "unsupported"
                assert result["fertilizer"] == "Reliable recommendation unavailable"
                assert result["mapped_crop_category"] is None
                assert "does not contain experimental data" in result["advice"]

    def test_empty_or_none_crop_fallback(self, app):
        with app.app_context():
            from app.ml.fertilizer_model import predict_fertilizer
            sensor = {"air_temperature": 28, "moisture": 50}

            r1 = predict_fertilizer(sensor, "Loamy", "", dict(app.config))
            assert r1["status"] == "unsupported"
            assert r1["crop"] is None

            r2 = predict_fertilizer(sensor, "Loamy", None, dict(app.config))
            assert r2["status"] == "unsupported"
            assert r2["crop"] is None

    def test_alluvial_soil_without_texture_withheld(self, app):
        """Alluvial soil without physical texture confirmation must withhold advice."""
        with app.app_context():
            from app.ml.fertilizer_model import predict_fertilizer
            sensor = {"air_temperature": 28, "moisture": 50}

            result = predict_fertilizer(sensor, "Alluvial", "wheat", dict(app.config))
            assert result["status"] == "unsupported"
            assert "physical texture confirmation required" in result["advice"] or "Alluvial" in result["advice"]

    def test_alluvial_soil_with_confirmed_texture_supported(self, app):
        """Alluvial soil with valid confirmed texture proceeds to prediction."""
        with app.app_context():
            from app.ml.fertilizer_model import predict_fertilizer
            sensor = {"air_temperature": 28, "air_humidity": 60, "moisture": 50,
                      "nitrogen": 45, "potassium": 160, "phosphorus": 25}

            result = predict_fertilizer(sensor, "Alluvial", "rice", dict(app.config), confirmed_texture="Clayey")
            assert result["status"] == "supported"
            assert "Alluvial soil recommendation based on confirmed physical texture" in result["advice"]
