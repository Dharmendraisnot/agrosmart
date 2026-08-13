"""
Prediction — stores one ML/rule-engine output record linked to a SoilAnalysis.
One analysis produces three Prediction rows: crop, fertilizer, irrigation.
"""
import json
from datetime import datetime, timezone
from app.extensions import db


class Prediction(db.Model):
    __tablename__ = "predictions"

    id                  = db.Column(db.Integer, primary_key=True)
    timestamp           = db.Column(db.DateTime, nullable=False,
                                    default=lambda: datetime.now(timezone.utc))

    # FK to the analysis that produced this prediction
    analysis_id         = db.Column(db.Integer,
                                    db.ForeignKey("soil_analyses.id"),
                                    nullable=False)

    # "crop" | "fertilizer" | "irrigation"
    prediction_type     = db.Column(db.String(30), nullable=False)

    # Full structured result stored as a JSON string
    _result_json        = db.Column("result_json", db.Text, nullable=False, default="{}")

    # Human-readable top recommendation (for quick display / history list)
    top_recommendation  = db.Column(db.String(200), nullable=True)

    # Which model/rule version produced this — e.g. "rf_v1.0", "prototype_kaggle_v1.0"
    model_version       = db.Column(db.String(50), nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    analysis = db.relationship("SoilAnalysis", back_populates="predictions")

    # ── JSON helpers ─────────────────────────────────────────────────────────
    @property
    def result(self) -> dict:
        """Return result_json as a Python dict."""
        try:
            return json.loads(self._result_json)
        except (TypeError, json.JSONDecodeError):
            return {}

    @result.setter
    def result(self, value: dict):
        self._result_json = json.dumps(value)

    def to_dict(self) -> dict:
        return {
            "id":                 self.id,
            "timestamp":          self.timestamp.isoformat(),
            "analysis_id":        self.analysis_id,
            "prediction_type":    self.prediction_type,
            "result":             self.result,
            "top_recommendation": self.top_recommendation,
            "model_version":      self.model_version,
        }

    def __repr__(self) -> str:
        return (f"<Prediction id={self.id} type={self.prediction_type} "
                f"model={self.model_version}>")
