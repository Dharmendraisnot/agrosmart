"""
conftest.py — shared pytest fixtures for AgroSmart backend tests.

Fixtures available to all test modules:
    app          — Flask app instance with TestingConfig (in-memory SQLite)
    client       — Flask test client
    db_session   — SQLAlchemy session within the app context
    sample_sensor_reading — a persisted SensorReading for FK tests
"""
import pytest
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import db as _db
from app.models.sensor_reading import SensorReading


@pytest.fixture(scope="session")
def app():
    """Create a Flask app using TestingConfig (in-memory SQLite)."""
    flask_app = create_app("testing")
    yield flask_app


@pytest.fixture(scope="session")
def _db_setup(app):
    """Create all DB tables once per test session, drop at the end."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


@pytest.fixture(scope="function")
def db_session(app, _db_setup):
    """
    Provide a clean DB session per test function.
    All writes are rolled back after each test so tests are independent.
    """
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()

        # Bind session to the connection so rollback works
        _db.session.bind = connection

        yield _db.session

        _db.session.remove()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(app):
    """Flask test client — no live server needed."""
    with app.test_client() as c:
        with app.app_context():
            _db.create_all()
            yield c


@pytest.fixture
def sample_sensor_reading(db_session):
    """Persist and return a SensorReading with realistic values."""
    reading = SensorReading(
        source           = "test",
        moisture         = 52.0,
        ph               = 6.5,
        soil_temperature = 24.0,
        air_temperature  = 30.0,
        air_humidity     = 65.0,
        nitrogen         = 40.0,
        phosphorus       = 20.0,
        potassium        = 180.0,
    )
    db_session.add(reading)
    db_session.commit()
    return reading
