"""
SoilAnalysis — links a SensorReading to the CNN soil classification result
and a computed health score.
"""
from datetime import datetime, timezone
from app.extensions import db


class SoilAnalysis(db.Model):
    __tablename__ = "soil_analyses"

    id                    = db.Column(db.Integer, primary_key=True)
    timestamp             = db.Column(db.DateTime, nullable=False,
                                      default=lambda: datetime.now(timezone.utc))

    # FK to the sensor snapshot this analysis is based on
    sensor_reading_id     = db.Column(db.Integer,
                                      db.ForeignKey("sensor_readings.id"),
                                      nullable=False)

    # Soil image path relative to uploads/
    soil_image_path       = db.Column(db.String(255), nullable=True)

    # CNN output
    soil_type             = db.Column(db.String(50),  nullable=True)   # Sandy/Clay/Loamy/Silty
    soil_type_confidence  = db.Column(db.Float,        nullable=True)   # 0.0–1.0

    # Composite health assessment
    soil_health_status    = db.Column(db.String(20),  nullable=True)   # Good / Fair / Poor
    health_score          = db.Column(db.Float,        nullable=True)   # 0–100

    notes                 = db.Column(db.Text, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    sensor_reading = db.relationship("SensorReading", back_populates="analyses")
    predictions    = db.relationship("Prediction",    back_populates="analysis",
                                     lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id":                   self.id,
            "timestamp":            self.timestamp.isoformat(),
            "sensor_reading_id":    self.sensor_reading_id,
            "soil_image_path":      self.soil_image_path,
            "soil_type":            self.soil_type,
            "soil_type_confidence": self.soil_type_confidence,
            "soil_health_status":   self.soil_health_status,
            "health_score":         self.health_score,
            "notes":                self.notes,
        }

    def __repr__(self) -> str:
        return f"<SoilAnalysis id={self.id} type={self.soil_type} health={self.soil_health_status}>"
