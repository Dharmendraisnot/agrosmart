"""
Models package — import all ORM models here so SQLAlchemy's metadata
is aware of every table before create_all() is called.
"""
from .sensor_reading import SensorReading
from .soil_analysis  import SoilAnalysis
from .prediction     import Prediction
from .user           import User

__all__ = ["SensorReading", "SoilAnalysis", "Prediction", "User"]
