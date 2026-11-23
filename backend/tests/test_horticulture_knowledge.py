"""
tests/test_horticulture_knowledge.py — Unit tests for the horticulture knowledge base.

Tests:
  - All 12 unsupported crops from the fertilizer audit are present and verified
  - Required schema fields exist for every crop entry
  - Authoritative sources are documented for every crop
  - Missing or unverified experimental fields are tracked
  - Case-insensitivity, whitespace, and alias resolution
  - Graceful handling of unknown, None, and empty crop queries
  - Immutability of the knowledge base through deepcopy
  - Dynamic age-based dose calculations for orchard trees
  - Separation from supported field crops (rice, maize, chickpea, etc.)
"""
import pytest
from app.ml.horticulture_knowledge import (
    HORTICULTURE_DATABASE,
    HORTICULTURE_ALIASES,
    is_horticultural_crop,
    get_horticulture_profile,
    list_supported_horticultural_crops,
    format_horticultural_advisory,
    normalize_crop_name,
)

AUDIT_12_CROPS = [
    "apple",
    "banana",
    "coconut",
    "coffee",
    "grapes",
    "jute",
    "mango",
    "muskmelon",
    "orange",
    "papaya",
    "pomegranate",
    "watermelon",
]

REQUIRED_SCHEMA_KEYS = [
    "crop_key",
    "common_name",
    "botanical_name",
    "plant_type",
    "verified",
    "authority_sources",
    "application_geometry",
    "dosage_unit",
    "annual_schedule",
    "timing_and_splits",
    "organic_manure",
    "micronutrients",
    "special_cautions",
    "missing_or_unverified_fields",
]


class TestHorticultureKnowledgeCoverage:
    """Verify presence and schema integrity of all 12 unsupported crops."""

    def test_all_12_audit_crops_are_registered(self):
        registered = list_supported_horticultural_crops()
        for crop in AUDIT_12_CROPS:
            assert crop in registered, f"Crop '{crop}' missing from horticulture database"

    def test_database_exact_count(self):
        assert len(HORTICULTURE_DATABASE) == 12

    @pytest.mark.parametrize("crop", AUDIT_12_CROPS)
    def test_crop_schema_keys(self, crop):
        profile = get_horticulture_profile(crop)
        assert profile is not None
        for key in REQUIRED_SCHEMA_KEYS:
            assert key in profile, f"Key '{key}' missing from profile for '{crop}'"

    @pytest.mark.parametrize("crop", AUDIT_12_CROPS)
    def test_sources_and_verification_flags(self, crop):
        profile = get_horticulture_profile(crop)
        assert profile["verified"] is True
        assert isinstance(profile["authority_sources"], list)
        assert len(profile["authority_sources"]) >= 1
        for src in profile["authority_sources"]:
            assert isinstance(src, str) and len(src) > 10

    @pytest.mark.parametrize("crop", AUDIT_12_CROPS)
    def test_missing_data_transparency(self, crop):
        profile = get_horticulture_profile(crop)
        assert "missing_or_unverified_fields" in profile
        assert isinstance(profile["missing_or_unverified_fields"], list)
        assert len(profile["missing_or_unverified_fields"]) >= 1

    @pytest.mark.parametrize("crop", AUDIT_12_CROPS)
    def test_application_geometry_and_splits_defined(self, crop):
        profile = get_horticulture_profile(crop)
        assert len(profile["application_geometry"]) > 20
        assert isinstance(profile["timing_and_splits"], list)
        assert len(profile["timing_and_splits"]) >= 1


class TestNameNormalizationAndAliases:
    """Verify case insensitivity, whitespace trimming, and alias resolution."""

    def test_case_and_whitespace_insensitivity(self):
        assert is_horticultural_crop("Mango") is True
        assert is_horticultural_crop("MANGO") is True
        assert is_horticultural_crop("  mango  ") is True
        assert is_horticultural_crop("bAnAnA") is True

    def test_alias_resolution(self):
        assert normalize_crop_name("citrus") == "orange"
        assert normalize_crop_name("mandarin") == "orange"
        assert normalize_crop_name("sweet orange") == "orange"
        assert normalize_crop_name("musk melon") == "muskmelon"
        assert normalize_crop_name("water melon") == "watermelon"
        assert normalize_crop_name("aam") == "mango"
        assert normalize_crop_name("tossa jute") == "jute"

    def test_is_horticultural_crop_via_aliases(self):
        assert is_horticultural_crop("citrus") is True
        assert is_horticultural_crop("sweet orange") is True
        assert is_horticultural_crop("musk melon") is True
        assert is_horticultural_crop("aam") is True


class TestMissingAndInvalidHandling:
    """Verify graceful handling of non-horticultural, unknown, or None inputs."""

    @pytest.mark.parametrize("invalid_input", [None, "", "   ", "unknown_crop", "xyz_fruit_123"])
    def test_invalid_crops_return_safe_defaults(self, invalid_input):
        assert is_horticultural_crop(invalid_input) is False
        assert get_horticulture_profile(invalid_input) is None
        assert format_horticultural_advisory(invalid_input) is None

    def test_supported_field_crops_are_not_in_horticulture_db(self):
        """Field crops handled by the Decision Tree must return False."""
        field_crops = ["rice", "maize", "wheat", "cotton", "kidneybeans", "chickpea", "lentil"]
        for crop in field_crops:
            assert is_horticultural_crop(crop) is False
            assert get_horticulture_profile(crop) is None


class TestAdvisoryFormattingAndAgeCalculations:
    """Verify advisory synthesis and dynamic age calculations."""

    def test_mango_advisory_structure(self):
        advisory = format_horticultural_advisory("mango")
        assert advisory is not None
        assert advisory["status"] == "horticultural_guideline"
        assert advisory["crop"] == "mango"
        assert advisory["botanical_name"] == "Mangifera indica"
        assert "Extension Package of Practices" in advisory["headline"]
        assert advisory["verified"] is True
        assert "canopy drip line" in advisory["application_method"]
        assert len(advisory["timing_and_splits"]) >= 2
        assert "STRICT CAUTION" in advisory["special_cautions"]

    def test_mango_tree_age_scaling(self):
        # Year 1 young tree
        adv_yr1 = format_horticultural_advisory("mango", tree_age_years=1)
        assert "Year 1 Young Tree" in adv_yr1["dosage_summary"]
        assert "10 kg FYM" in adv_yr1["dosage_summary"]
        assert "100g N" in adv_yr1["dosage_summary"]

        # Year 5 intermediate tree: 100 + 4*100 = 500g N, 10 + 4*5 = 30 kg FYM
        adv_yr5 = format_horticultural_advisory("mango", tree_age_years=5)
        assert "Tree Age 5: 30 kg FYM, 500g N, 250g P2O5, 500g K2O" in adv_yr5["dosage_summary"]

        # Year 10 mature tree
        adv_yr10 = format_horticultural_advisory("mango", tree_age_years=10)
        assert "Mature Tree (Age 10+)" in adv_yr10["dosage_summary"]
        assert "1000g N" in adv_yr10["dosage_summary"]
        assert "50 kg FYM" in adv_yr10["dosage_summary"]

    def test_banana_per_plant_advisory(self):
        adv = format_horticultural_advisory("banana")
        assert adv["dosage_unit"] == "per_plant_per_cycle"
        assert "200g N" in adv["dosage_summary"]
        assert "300g K2O" in adv["dosage_summary"]

    def test_grapes_chloride_caution(self):
        adv = format_horticultural_advisory("grapes")
        assert "CHLORIDE" in adv["special_cautions"]
        assert "Sulfate of Potash" in adv["special_cautions"]

    def test_coconut_potassium_and_magnesium_guidelines(self):
        adv = format_horticultural_advisory("coconut")
        assert adv["dosage_unit"] == "per_palm_per_year"
        assert "1200g K2O" in adv["dosage_summary"]


class TestImmutability:
    """Verify that consumer cannot inadvertently mutate the module database."""

    def test_profile_mutation_does_not_affect_database(self):
        p1 = get_horticulture_profile("mango")
        p1["common_name"] = "Corrupted Name"
        p1["authority_sources"].clear()

        p2 = get_horticulture_profile("mango")
        assert p2["common_name"] == "Mango"
        assert len(p2["authority_sources"]) > 0
