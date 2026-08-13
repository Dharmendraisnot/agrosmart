"""
API package.
Each blueprint is imported here and returned by register_blueprints()
so the app factory stays clean.
"""
from .health import health_bp

__all__ = ["health_bp"]
