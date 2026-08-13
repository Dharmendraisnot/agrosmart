# AgroSmart — AI-Based Soil Analysis & Crop Recommendation System

B.Tech AI/ML Minor Project

---

## Project Overview

AgroSmart is a full-stack web application connected to a Raspberry Pi 5 soil
analysis system. It reads real-time soil sensor data, classifies soil type via
CNN, and produces AI-driven recommendations for crop selection, fertilizer
application, and irrigation scheduling.

**Tech stack:** Python Flask · SQLite · scikit-learn · TensorFlow/Keras · React · Vite · Tailwind CSS

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Git

### 1. Clone and set up backend

```bash
git clone <repo-url>
cd agrosmart/backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env if needed — defaults work for development
```

### 2. Train ML models (first-time setup)

```bash
# Generate synthetic training data (mirrors Kaggle schema)
python ml_training/generate_synthetic_datasets.py

# Train crop recommendation model (Random Forest)
python ml_training/train_crop_model.py

# Train fertilizer model (Decision Tree — prototype)
python ml_training/train_fertilizer_model.py
```

> To use real Kaggle datasets instead, see `ml_training/datasets/README.md`.

### 3. Start the backend

```bash
python run.py
# API available at http://localhost:5000
# Verify: curl http://localhost:5000/api/health
```

### 4. Set up and start the frontend

```bash
cd ../frontend
npm install
npm run dev
# Dashboard at http://localhost:3000
```

---

## System Architecture

```
Simulator HAL  ←──(SENSOR_MODE=simulator)
     │
     ▼
sensor_service  ──→  SQLite DB
     │
     ▼
analysis_service
  ├── crop_model.py    (Random Forest)
  ├── fertilizer_model.py (Decision Tree)
  ├── soil_cnn.py      (MobileNetV2 CNN)
  └── recommendation_service.py (irrigation rules)
     │
     ▼
Flask REST API  ←──→  React Dashboard
```

---

## Project Structure

```
agrosmart/
├── backend/
│   ├── app/
│   │   ├── api/            # Flask route blueprints
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── services/       # Business logic
│   │   ├── ml/             # ML inference wrappers
│   │   └── hardware/       # HAL: simulator + Raspberry Pi
│   ├── ml_training/        # Training scripts + datasets
│   ├── trained_models/     # Saved model files (.pkl, .h5)
│   ├── tests/              # pytest test suite
│   ├── docs/               # Documentation
│   └── pi_sensor_tests/    # Hardware validation scripts
├── frontend/
│   └── src/
│       ├── pages/          # 6 route pages
│       ├── components/     # UI components
│       ├── hooks/          # Data-fetching hooks
│       └── services/       # API calls (axios)
└── docs/
    ├── hardware-setup.md   # GPIO wiring + calibration guide
    ├── api-reference.md    # Full REST API documentation
    └── ml-pipeline.md      # Model training + evaluation guide
```

---

## ML Models

| Model | Algorithm | Dataset | Accuracy |
|-------|-----------|---------|----------|
| Crop Recommendation | Random Forest (100 trees) | Kaggle / AgroSmart (Phase 5) | Evaluated after training |
| Fertilizer Recommendation | Decision Tree (prototype) | Kaggle ⚠ | Evaluated after training |
| Soil Classification | MobileNetV2 CNN | Soil image dataset | Evaluated after training |
| Irrigation Advice | Rule engine | — | Deterministic |

> Accuracy figures are computed by `evaluate_models.py` after actual training.
> They are never hardcoded.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | System health + sensor mode |
| GET | `/api/sensors/latest` | Fresh sensor reading |
| GET | `/api/sensors/history` | Paginated history |
| POST | `/api/sensors/reading` | Manual sensor submit |
| POST | `/api/analysis/run` | Run full AI pipeline |
| GET | `/api/analysis/<id>` | Get one analysis |
| GET | `/api/analysis/history` | Analysis history |
| GET | `/api/predictions/latest` | Latest predictions |
| GET | `/api/predictions/history` | Prediction history |
| POST | `/api/images/upload` | Upload soil image (CNN) |
| GET | `/api/images/<filename>` | Serve uploaded image |

Full documentation: `docs/api-reference.md`

---

## Running Tests

```bash
cd agrosmart/backend
python -m pytest tests/ -v
```

Expected: **93 tests, 0 failures**

---

## Switching to Real Raspberry Pi Hardware

1. Follow the wiring guide in `docs/hardware-setup.md`
2. Enable SPI, I2C, 1-Wire, Camera on the Pi via `raspi-config`
3. Install Pi dependencies: `pip install -r requirements-pi.txt`
4. Run sensor tests: `python pi_sensor_tests/test_all_sensors.py`
5. Set in `.env`: `SENSOR_MODE=hardware`
6. Restart the Flask server

---

## Development Workflow

```bash
# Backend — simulator mode (default)
cd backend && python run.py

# Frontend — Vite dev server with API proxy
cd frontend && npm run dev

# Run tests
cd backend && python -m pytest

# Retrain a model
cd backend && python ml_training/train_crop_model.py

# Evaluate all models
cd backend && python ml_training/evaluate_models.py --model all
```

---

## Environment Variables

See `backend/.env.example` for all options.

Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SENSOR_MODE` | `simulator` | `simulator` or `hardware` |
| `FLASK_ENV` | `development` | `development`, `testing`, `production` |
| `SECRET_KEY` | (change this) | Flask secret key |
| `CROP_MODEL_PATH` | `trained_models/crop_rf_v1.pkl` | Path to crop RF model |
| `FERTILIZER_MODEL_PATH` | `trained_models/fertilizer_dt_prototype.pkl` | Active fertilizer model |
| `FERTILIZER_MODEL_LABEL` | `prototype_kaggle_v1.0` | Label recorded in DB |

---

## License

B.Tech Minor Project — Academic use only.
