"""
Flask extension instances.
Initialised here without an app so they can be imported anywhere,
then bound to the app inside create_app() via .init_app(app).
"""
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db   = SQLAlchemy()
cors = CORS()
