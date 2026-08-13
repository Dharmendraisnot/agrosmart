"""
SimulatedSensor — implements SensorInterface with numpy-based random values.

Design goals:
  - Values stay within agronomically realistic ranges at all times.
  - A gentle sinusoidal drift is added so dashboard charts show meaningful
    variation over time (not just flat noise).
  - read_all() overrides the base implementation to generate one consistent
    snapshot (all values correlated to the same time seed).
  - No hardware libraries are imported here.
"""
from __future__ import annotations

import math
import time
import random

from .hal import SensorInterface

# ── Realistic agronomic ranges ────────────────────────────────────────────────
# (min, max, baseline)  — baseline is the midpoint the drift oscillates around

_RANGES = {
    "moisture":         (20.0,  85.0,  52.0),   # % volumetric water content
    "ph":               (4.5,    8.5,   6.5),   # pH scale
    "soil_temperature": (10.0,  40.0,  26.0),   # °C
    "air_temperature":  (15.0,  45.0,  30.0),   # °C
    "air_humidity":     (30.0,  95.0,  62.0),   # %
    "nitrogen":         (5.0,   90.0,  40.0),   # mg/kg
    "phosphorus":       (2.0,   55.0,  22.0),   # mg/kg
    "potassium":        (40.0, 350.0, 180.0),   # mg/kg
}

# Noise amplitude as a fraction of (max-min)
_NOISE_FRACTION = 0.04

# Drift cycle period in seconds (10 min → values complete one full sine cycle)
_DRIFT_PERIOD = 600.0


class SimulatedSensor(SensorInterface):
    """
    Produces realistic simulated sensor readings.

    Each reading = baseline + slow sinusoidal drift + small random noise,
    clamped to [min, max].  The drift uses the wall-clock time so values
    change smoothly when the frontend polls every 10 seconds.
    """

    def __init__(self, seed: int | None = None):
        # Optional seed for deterministic output in tests
        self._rng = random.Random(seed)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _generate(self, key: str) -> float:
        lo, hi, base = _RANGES[key]
        span = hi - lo

        # Slow sinusoidal drift (period = _DRIFT_PERIOD seconds)
        drift = (span * 0.25) * math.sin(2 * math.pi * time.time() / _DRIFT_PERIOD)

        # Small random noise
        noise = self._rng.uniform(-span * _NOISE_FRACTION, span * _NOISE_FRACTION)

        value = base + drift + noise
        return round(max(lo, min(hi, value)), 2)

    # ── SensorInterface implementation ────────────────────────────────────────

    def read_moisture(self) -> float:
        return self._generate("moisture")

    def read_ph(self) -> float:
        return self._generate("ph")

    def read_soil_temperature(self) -> float:
        return self._generate("soil_temperature")

    def read_air_temperature(self) -> float:
        return self._generate("air_temperature")

    def read_air_humidity(self) -> float:
        return self._generate("air_humidity")

    def read_npk(self) -> dict:
        return {
            "nitrogen":   self._generate("nitrogen"),
            "phosphorus": self._generate("phosphorus"),
            "potassium":  self._generate("potassium"),
        }

    def read_all(self) -> dict:
        """
        Override: generate all values from a single time snapshot so the
        returned dict is internally consistent (all values from the same
        simulated instant, not eight separate calls at slightly different times).
        """
        npk = self.read_npk()
        return {
            "moisture":         self.read_moisture(),
            "ph":               self.read_ph(),
            "soil_temperature": self.read_soil_temperature(),
            "air_temperature":  self.read_air_temperature(),
            "air_humidity":     self.read_air_humidity(),
            "nitrogen":         npk["nitrogen"],
            "phosphorus":       npk["phosphorus"],
            "potassium":        npk["potassium"],
        }
