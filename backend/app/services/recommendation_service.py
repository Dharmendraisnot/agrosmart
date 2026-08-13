"""
services/recommendation_service.py — Rule-based irrigation advice engine.

No ML model file required. All logic is explicit, deterministic, and
adjustable via the threshold constants at the top of this file.

The irrigation decision uses:
  1. Soil moisture level (primary driver)
  2. Soil type (clay retains more, sandy drains faster)
  3. Crop water requirement tier (where crop is known)
  4. Air temperature (evapotranspiration adjustment)
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ── Thresholds (%) ────────────────────────────────────────────────────────────
CRITICAL_LOW  = 25.0   # Irrigate immediately
LOW           = 40.0   # Irrigate within 24 h
ADEQUATE      = 60.0   # Monitor
HIGH          = 75.0   # No irrigation needed

# ── Soil type drainage modifiers ──────────────────────────────────────────────
# Sandy drains fast → effective moisture is lower than measured
# Clay retains water → effective moisture is higher than measured
_SOIL_MODIFIER = {
    "Sandy": -8.0,
    "Loamy":  0.0,   # baseline
    "Silty": +3.0,
    "Clay":  +8.0,
}

# ── Crop water requirement tiers ──────────────────────────────────────────────
# "high" crops need more water → tighten thresholds by +5%
# "low"  crops need less        → relax thresholds by -5%
_CROP_WATER_TIER: dict[str, str] = {
    "rice":        "high",
    "sugarcane":   "high",
    "banana":      "high",
    "coconut":     "high",
    "maize":       "medium",
    "wheat":       "medium",
    "cotton":      "medium",
    "jute":        "medium",
    "chickpea":    "low",
    "lentil":      "low",
    "mungbean":    "low",
    "mothbeans":   "low",
    "pigeonpeas":  "low",
    "kidneybeans": "low",
    "blackgram":   "low",
}
_TIER_ADJUST = {"high": +5.0, "medium": 0.0, "low": -5.0}


def _effective_moisture(moisture: float, soil_type: str | None,
                        crop: str | None) -> float:
    """Apply soil-type and crop-tier adjustments to raw moisture %."""
    soil_adj = _SOIL_MODIFIER.get(soil_type or "Loamy", 0.0)
    tier      = _CROP_WATER_TIER.get((crop or "").lower(), "medium")
    crop_adj  = _TIER_ADJUST[tier]
    return moisture + soil_adj - crop_adj   # note: crop adjust adds demand


def _temperature_warning(air_temp: float | None) -> str | None:
    """Return an advisory if high temperature suggests extra evapotranspiration."""
    if air_temp is None:
        return None
    if air_temp > 38:
        return "High air temperature detected — increase irrigation frequency."
    if air_temp > 32:
        return "Warm conditions — monitor soil moisture more frequently."
    return None


def generate_irrigation_advice(sensor: dict, soil_type: str | None = None,
                                top_crop: str | None = None) -> dict:
    """
    Generate irrigation advice from sensor readings.

    Args:
        sensor:    sensor reading dict (moisture, air_temperature, etc.)
        soil_type: CNN-predicted soil type (optional — defaults to Loamy)
        top_crop:  top-1 crop recommendation (optional)

    Returns:
        {
          "action":           "Irrigate immediately",
          "urgency":          "critical" | "high" | "medium" | "low" | "none",
          "frequency":        "Every day",
          "estimated_water":  "30 L/m²",
          "effective_moisture": 32.5,
          "raw_moisture":     38.0,
          "temperature_note": "..." | None,
          "reasoning":        "..."
        }
    """
    raw_moisture = sensor.get("moisture")
    air_temp     = sensor.get("air_temperature")

    # Guard: if moisture is missing, return advisory-only response
    if raw_moisture is None:
        return {
            "action":            "Moisture sensor unavailable — inspect manually",
            "urgency":           "unknown",
            "frequency":         "N/A",
            "estimated_water":   "N/A",
            "effective_moisture": None,
            "raw_moisture":      None,
            "temperature_note":  None,
            "reasoning":         "Moisture reading was NULL — cannot determine irrigation need.",
        }

    eff = _effective_moisture(raw_moisture, soil_type, top_crop)
    temp_note = _temperature_warning(air_temp)

    # Decision table
    if eff < CRITICAL_LOW:
        action   = "Irrigate immediately"
        urgency  = "critical"
        freq     = "Twice daily until moisture recovers"
        water    = "35 L/m²"
        reason   = f"Effective moisture {eff:.1f}% is critically low (< {CRITICAL_LOW}%)."
    elif eff < LOW:
        action   = "Irrigate within 24 hours"
        urgency  = "high"
        freq     = "Every day"
        water    = "25 L/m²"
        reason   = f"Effective moisture {eff:.1f}% is low (< {LOW}%)."
    elif eff < ADEQUATE:
        action   = "Monitor — soil moisture is adequate"
        urgency  = "medium"
        freq     = "Every 2–3 days"
        water    = "15 L/m²"
        reason   = f"Effective moisture {eff:.1f}% is in the adequate range ({LOW}–{ADEQUATE}%)."
    elif eff < HIGH:
        action   = "No irrigation needed"
        urgency  = "low"
        freq     = "Check again in 3–4 days"
        water    = "0 L/m²"
        reason   = f"Effective moisture {eff:.1f}% is good ({ADEQUATE}–{HIGH}%)."
    else:
        action   = "No irrigation — soil is well saturated"
        urgency  = "none"
        freq     = "Check again in 5–7 days"
        water    = "0 L/m²"
        reason   = f"Effective moisture {eff:.1f}% is high (> {HIGH}%). Risk of waterlogging."

    return {
        "action":            action,
        "urgency":           urgency,
        "frequency":         freq,
        "estimated_water":   water,
        "effective_moisture": round(eff, 2),
        "raw_moisture":      round(raw_moisture, 2),
        "temperature_note":  temp_note,
        "reasoning":         reason,
    }
