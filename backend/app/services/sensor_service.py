"""
SensorService — reads from the HAL and persists SensorReading records.

Responsibilities:
  - Ask the HAL for a reading (simulator or hardware).
  - Perform range validation / sanity checks.
  - Write the reading to the database.
  - Return the ORM object (or its dict) to the caller.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from flask import current_app

from app.extensions import db
from app.models.sensor_reading import SensorReading
from app.hardware.hal import get_sensor, SensorReadError

logger = logging.getLogger(__name__)

# ── Acceptable value ranges for validation ────────────────────────────────────
_VALID_RANGES: dict[str, tuple[float, float]] = {
    "moisture":         (0.0,   100.0),
    "ph":               (0.0,    14.0),
    "soil_temperature": (-10.0,  80.0),
    "air_temperature":  (-20.0,  80.0),
    "air_humidity":     (0.0,   100.0),
    "nitrogen":         (0.0,  1000.0),
    "phosphorus":       (0.0,  1000.0),
    "potassium":        (0.0,  2000.0),
}


def _clamp_or_none(value: float | None, key: str) -> float | None:
    """
    If value is outside the physical valid range, log a warning and return None
    rather than persisting a garbage reading. None values are stored as NULL.
    """
    if value is None:
        return None
    lo, hi = _VALID_RANGES[key]
    if not (lo <= value <= hi):
        logger.warning("Sensor value out of range: %s=%.2f (expected %.1f–%.1f)",
                       key, value, lo, hi)
        return None
    return value


def capture_reading() -> SensorReading:
    """
    Read all sensors via the HAL, validate the values, persist to DB, and
    return the saved SensorReading ORM instance.

    Raises:
        SensorReadError: if the underlying sensor (real or simulated) fails.
    """
    mode   = current_app.config.get("SENSOR_MODE", "simulator")
    sensor = get_sensor(mode)

    raw = sensor.read_all()
    logger.debug("Raw sensor reading: %s", raw)

    reading = SensorReading(
        timestamp        = datetime.now(timezone.utc),
        source           = mode,
        moisture         = _clamp_or_none(raw.get("moisture"),         "moisture"),
        ph               = _clamp_or_none(raw.get("ph"),               "ph"),
        soil_temperature = _clamp_or_none(raw.get("soil_temperature"), "soil_temperature"),
        air_temperature  = _clamp_or_none(raw.get("air_temperature"),  "air_temperature"),
        air_humidity     = _clamp_or_none(raw.get("air_humidity"),     "air_humidity"),
        nitrogen         = _clamp_or_none(raw.get("nitrogen"),         "nitrogen"),
        phosphorus       = _clamp_or_none(raw.get("phosphorus"),       "phosphorus"),
        potassium        = _clamp_or_none(raw.get("potassium"),        "potassium"),
    )

    db.session.add(reading)
    db.session.commit()

    logger.info("SensorReading id=%d saved (source=%s)", reading.id, reading.source)
    return reading


def get_latest_reading() -> SensorReading | None:
    """Return the most recent SensorReading from the database, or None."""
    return (
        db.session.query(SensorReading)
        .order_by(SensorReading.timestamp.desc())
        .first()
    )


def get_reading_history(page: int = 1, per_page: int = 50) -> dict:
    """
    Return a paginated list of SensorReadings (newest first).

    Returns a dict compatible with the API response schema:
    {
        "items":    [...],
        "total":    int,
        "page":     int,
        "per_page": int,
        "pages":    int,
    }
    """
    pagination = (
        db.session.query(SensorReading)
        .order_by(SensorReading.timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return {
        "items":    [r.to_dict() for r in pagination.items],
        "total":    pagination.total,
        "page":     pagination.page,
        "per_page": pagination.per_page,
        "pages":    pagination.pages,
    }
