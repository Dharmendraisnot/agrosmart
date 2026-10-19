"""
ml/fertilizer_model.py — Fertilizer recommendation inference wrapper.

Supports two model lifecycle stages (set via config):
  prototype_kaggle_v1.0  →  fertilizer_dt_prototype.pkl  (Kaggle data)
  final_agrosmart_v1.0   →  fertilizer_dt_final.pkl       (real AgroSmart data)

The active model is selected by FERTILIZER_MODEL_PATH in .env / config.py.
To switch, change FERTILIZER_MODEL_PATH and FERTILIZER_MODEL_LABEL — nothing
else in the codebase needs to change.

Usage:
    from app.ml.fertilizer_model import predict_fertilizer
    result = predict_fertilizer(sensor_dict, soil_type, top_crop, config)
"""
from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np

from app.ml.preprocessor import FertilizerInferencePreprocessor

logger = logging.getLogger(__name__)

_model        = None
_preprocessor: FertilizerInferencePreprocessor | None = None
_model_label  = None


def _load(config: dict) -> None:
    """Load model + scaler + encoders. Called once per process."""
    global _model, _preprocessor, _model_label

    model_path    = Path(config["FERTILIZER_MODEL_PATH"])
    scaler_path   = model_path.parent / "fertilizer_scaler.pkl"
    encoders_path = model_path.parent / "fertilizer_encoders.pkl"
    _model_label  = config.get("FERTILIZER_MODEL_LABEL", "unknown")

    if not model_path.exists():
        raise FileNotFoundError(
            f"Fertilizer model not found: {model_path}\n"
            "Run: python ml_training/train_fertilizer_model.py"
        )

    _model        = joblib.load(model_path)
    _preprocessor = FertilizerInferencePreprocessor(scaler_path, encoders_path)
    logger.info("Fertilizer model loaded from %s  [label=%s]",
                model_path, _model_label)


# ── Human-readable NPK advice keyed by fertilizer name ────────────────────────
_FERTILIZER_ADVICE = {
    "Urea":      "Apply 50 kg/acre. Urea is high in nitrogen — ideal for leafy growth.",
    "DAP":       "Apply 50 kg/acre. DAP provides phosphorus for root development.",
    "14-35-14":  "Apply 50 kg/acre. Balanced with high phosphorus for flowering crops.",
    "28-28":     "Apply 40 kg/acre. Equal N and P — good for general crop health.",
    "17-17-17":  "Apply 50 kg/acre. Fully balanced NPK for maintenance fertilisation.",
    "20-20":     "Apply 45 kg/acre. Balanced N and P — suitable for most soil types.",
    "10-26-26":  "Apply 50 kg/acre. High P and K — ideal for fruiting and root crops.",
}


# ── Scientifically justified mapping from crop names to fertilizer dataset classes ──
# Only crops with genuine botanical or agronomic equivalence to the 12 Kaggle classes are mapped.
SCIENTIFIC_CROP_MAP = {
    # Direct species matches & agricultural synonyms
    "rice":        "Paddy",
    "paddy":       "Paddy",
    "wheat":       "Wheat",
    "barley":      "Barley",
    "maize":       "Maize",
    "millets":     "Millets",
    "cotton":      "Cotton",
    "kidneybeans": "Kidneybeans",
    "sugarcane":   "Sugarcane",
    "tobacco":     "Tobacco",
    "ground nuts": "Ground Nuts",
    "groundnut":   "Ground Nuts",
    "pulses":      "Pulses",
    "oil seeds":   "Oil seeds",
    "oilseeds":    "Oil seeds",

    # True leguminous grain pulses (Fabaceae family, biological nitrogen fixation)
    "chickpea":    "Pulses",
    "lentil":      "Pulses",
    "blackgram":   "Pulses",
    "mungbean":    "Pulses",
    "mothbeans":   "Pulses",
    "pigeonpeas":  "Pulses",
}


# Supported soil types in the fertilizer dataset
VALID_FERTILIZER_SOIL_TEXTURES = {
    "black":  "Black",
    "clayey": "Clayey",
    "clay":   "Clayey",
    "loamy":  "Loamy",
    "red":    "Red",
    "sandy":  "Sandy",
}


def predict_fertilizer(sensor: dict, soil_type: str,
                       top_crop: str, config: dict,
                       confirmed_texture: str | None = None) -> dict:
    """
    Predict the recommended fertilizer for the given soil + crop combination.

    If the crop is not scientifically supported by the 12-class fertilizer dataset,
    it returns an explicit 'Reliable recommendation unavailable' response rather
    than fabricating a recommendation by forcing an unrelated crop category.

    If the soil is Alluvial, fertilizer recommendations are withheld unless the
    user explicitly supplies a confirmed physical soil texture (e.g. Sandy, Clayey, Loamy).

    Args:
        sensor:            sensor reading dict
        soil_type:         CNN-predicted soil type (e.g. "Loamy", "Alluvial")
        top_crop:          top-1 crop recommendation (e.g. "wheat")
        config:            Flask app.config dict
        confirmed_texture: optional user-confirmed physical soil texture

    Returns:
        dict with fertilizer, advice, model_label, soil_type, crop, mapped_crop_category, status
    """
    global _model, _preprocessor, _model_label
    if _model is None:
        _load(config)

    crop_lower = (top_crop or "").strip().lower()
    soil_lower = (soil_type or "").strip().lower()

    # Check if the soil type is Alluvial
    if soil_lower == "alluvial":
        if confirmed_texture:
            conf_norm = confirmed_texture.strip().lower()
            if conf_norm in VALID_FERTILIZER_SOIL_TEXTURES:
                mapped_soil = VALID_FERTILIZER_SOIL_TEXTURES[conf_norm]
                logger.info(
                    "Alluvial soil recommendation proceeding with user-confirmed texture '%s' -> '%s'",
                    confirmed_texture, mapped_soil,
                )
            else:
                valid_list = sorted(list(set(VALID_FERTILIZER_SOIL_TEXTURES.values())))
                logger.warning("Invalid confirmed texture '%s' for Alluvial soil. Supported: %s",
                               confirmed_texture, valid_list)
                return {
                    "fertilizer":           "Reliable recommendation unavailable",
                    "advice": (
                        f"The confirmed texture '{confirmed_texture}' is not among the supported "
                        f"fertilizer categories: {valid_list}. Recommendation withheld."
                    ),
                    "model_label":          _model_label,
                    "soil_type":            soil_type,
                    "crop":                 top_crop,
                    "mapped_crop_category": None,
                    "status":               "unsupported",
                }
        else:
            logger.info(
                "Fertilizer prediction withheld for soil type 'Alluvial' (physical texture confirmation required)"
            )
            return {
                "fertilizer":           "Reliable recommendation unavailable",
                "advice": (
                    "The soil was classified as Alluvial. Because alluvial deposits vary widely in "
                    "physical texture (ranging from coarse sandy alluvium to heavy clayey alluvium), "
                    "automated fertilizer recommendations are withheld until soil texture is confirmed "
                    "by laboratory testing or user input."
                ),
                "model_label":          _model_label,
                "soil_type":            soil_type,
                "crop":                 top_crop,
                "mapped_crop_category": None,
                "status":               "unsupported",
            }
    else:
        mapped_soil = VALID_FERTILIZER_SOIL_TEXTURES.get(soil_lower, soil_type)

    # Check if the crop has a scientifically justified counterpart in the training data
    if crop_lower not in SCIENTIFIC_CROP_MAP:
        logger.info(
            "Fertilizer prediction withheld for unsupported crop '%s' (no valid dataset counterpart)",
            top_crop,
        )
        return {
            "fertilizer":           "Reliable recommendation unavailable",
            "advice": (
                f"The fertilizer training dataset does not contain experimental data for "
                f"'{top_crop.title()}'. Automated fertilizer recommendations are withheld "
                f"to preserve scientific accuracy. Please consult local agricultural extension "
                f"guidelines for this crop."
            ),
            "model_label":          _model_label,
            "soil_type":            soil_type,
            "crop":                 top_crop,
            "mapped_crop_category": None,
            "status":               "unsupported",
        }

    mapped_crop = SCIENTIFIC_CROP_MAP[crop_lower]
    X = _preprocessor.transform(sensor, soil_type=mapped_soil, crop_type=mapped_crop)
    prediction   = _model.predict(X)[0]
    fertilizer   = str(prediction)
    base_advice  = _FERTILIZER_ADVICE.get(
        fertilizer, f"Apply {fertilizer} as directed on the product label."
    )
    if soil_lower == "alluvial" and confirmed_texture:
        advice = f"{base_advice} (Note: Alluvial soil recommendation based on confirmed physical texture: '{mapped_soil}')"
    else:
        advice = base_advice

    result = {
        "fertilizer":           fertilizer,
        "advice":               advice,
        "model_label":          _model_label,
        "soil_type":            soil_type,
        "crop":                 top_crop,
        "mapped_crop_category": mapped_crop,
        "status":               "supported",
    }
    logger.debug("Fertilizer prediction: %s", result)
    return result


def reload_model() -> None:
    """Force model reload on the next predict call."""
    global _model, _preprocessor, _model_label
    _model = _preprocessor = _model_label = None
    logger.info("Fertilizer model cache cleared — will reload on next call")
