"""
User — optional authentication model.
Authentication is DISABLED for the MVP (open access dashboard).
This model is scaffolded here so it can be enabled in a future phase
without a schema change.
"""
from datetime import datetime, timezone
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # "admin" | "viewer"
    role         = db.Column(db.String(20), nullable=False, default="viewer")
    created_at   = db.Column(db.DateTime, nullable=False,
                             default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        # Never include password_hash in API responses
        return {
            "id":         self.id,
            "username":   self.username,
            "role":       self.role,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username} role={self.role}>"
