"""
SensorReading — stores one complete set of sensor values from either the
simulator or real Raspberry Pi hardware.
"""
from datetime import datetime, timezone
from app.extensions import db


class SensorReading(db.Model):
    __tablename__ = "sensor_readings"

    id               = db.Column(db.Integer, primary_key=True)
    timestamp        = db.Column(db.DateTime, nullable=False,
                                 default=lambda: datetime.now(timezone.utc))
    # "simulator" or "hardware"
    source           = db.Column(db.String(20), nullable=False, default="simulator")

    # ── Soil sensors ────────────────────────────────────────────────────────
    moisture         = db.Column(db.Float, nullable=True)   # % (0–100)
    ph               = db.Column(db.Float, nullable=True)   # pH (0–14)
    soil_temperature = db.Column(db.Float, nullable=True)   # °C

    # ── Ambient sensors (DHT22) ─────────────────────────────────────────────
    air_temperature  = db.Column(db.Float, nullable=True)   # °C
    air_humidity     = db.Column(db.Float, nullable=True)   # %

    # ── NPK sensor ──────────────────────────────────────────────────────────
    nitrogen         = db.Column(db.Float, nullable=True)   # mg/kg
    phosphorus       = db.Column(db.Float, nullable=True)   # mg/kg
    potassium        = db.Column(db.Float, nullable=True)   # mg/kg

    # ── Relationships ────────────────────────────────────────────────────────
    analyses = db.relationship("SoilAnalysis", back_populates="sensor_reading",
                                lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id":               self.id,
            "timestamp":        self.timestamp.isoformat(),
            "source":           self.source,
            "moisture":         self.moisture,
            "ph":               self.ph,
            "soil_temperature": self.soil_temperature,
            "air_temperature":  self.air_temperature,
            "air_humidity":     self.air_humidity,
            "nitrogen":         self.nitrogen,
            "phosphorus":       self.phosphorus,
            "potassium":        self.potassium,
        }

    def __repr__(self) -> str:
        return f"<SensorReading id={self.id} source={self.source} ts={self.timestamp}>"
