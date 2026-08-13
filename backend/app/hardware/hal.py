"""
Hardware Abstraction Layer (HAL) — interface definition and factory.

All application code reads sensors exclusively through this module.
The concrete implementation (simulator vs real hardware) is selected
at startup based on the SENSOR_MODE config value:

    SENSOR_MODE=simulator  →  SimulatedSensor   (Phase 1–4, dev)
    SENSOR_MODE=hardware   →  RaspberryPiSensor  (Phase 5, real Pi)

Nothing outside this package should ever import raspberry_pi.py directly.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SensorInterface(ABC):
    """
    Abstract contract that every sensor backend must satisfy.
    Each method returns a single float reading, or raises SensorReadError.
    read_all() returns a dict with every sensor value in one call.
    """

    @abstractmethod
    def read_moisture(self) -> float:
        """Soil volumetric moisture content (%)."""

    @abstractmethod
    def read_ph(self) -> float:
        """Soil pH (0–14 scale)."""

    @abstractmethod
    def read_soil_temperature(self) -> float:
        """Soil temperature in °C (DS18B20)."""

    @abstractmethod
    def read_air_temperature(self) -> float:
        """Ambient air temperature in °C (DHT22)."""

    @abstractmethod
    def read_air_humidity(self) -> float:
        """Ambient relative humidity % (DHT22)."""

    @abstractmethod
    def read_npk(self) -> dict:
        """
        NPK nutrient levels.
        Returns: {"nitrogen": float, "phosphorus": float, "potassium": float}
        Units: mg/kg (ppm).
        """

    def read_all(self) -> dict:
        """
        Read every sensor in one call and return a unified dict.
        Concrete subclasses may override this for efficiency (e.g. single
        UART burst read on the Pi), but the default implementation simply
        calls each individual reader.
        """
        npk = self.read_npk()
        return {
            "moisture":         self.read_moisture(),
            "ph":               self.read_ph(),
            "soil_temperature": self.read_soil_temperature(),
            "air_temperature":  self.read_air_temperature(),
            "air_humidity":     self.read_air_humidity(),
            "nitrogen":         npk.get("nitrogen"),
            "phosphorus":       npk.get("phosphorus"),
            "potassium":        npk.get("potassium"),
        }


class SensorReadError(RuntimeError):
    """Raised when a sensor read fails (timeout, hardware fault, etc.)."""


# ── Factory ───────────────────────────────────────────────────────────────────

_sensor_instance: SensorInterface | None = None


def get_sensor(mode: str = "simulator") -> SensorInterface:
    """
    Return (and cache) the appropriate SensorInterface implementation.

    Args:
        mode: "simulator" or "hardware"

    The instance is cached so sensors are only initialised once per process.
    """
    global _sensor_instance

    if _sensor_instance is not None:
        return _sensor_instance

    if mode == "hardware":
        # Import is intentionally deferred — this module must never be imported
        # on non-Pi machines where RPi.GPIO is unavailable.
        try:
            from .raspberry_pi import RaspberryPiSensor
            _sensor_instance = RaspberryPiSensor()
            logger.info("HAL: RaspberryPiSensor initialised (hardware mode)")
        except ImportError as exc:
            raise ImportError(
                "SENSOR_MODE=hardware requires RPi hardware libraries. "
                "Install requirements-pi.txt on a Raspberry Pi, "
                "or set SENSOR_MODE=simulator for development."
            ) from exc
    else:
        from .simulator import SimulatedSensor
        _sensor_instance = SimulatedSensor()
        logger.info("HAL: SimulatedSensor initialised (simulator mode)")

    return _sensor_instance


def reset_sensor() -> None:
    """
    Clear the cached sensor instance.
    Used in tests to force re-initialisation with a different mode.
    """
    global _sensor_instance
    _sensor_instance = None
