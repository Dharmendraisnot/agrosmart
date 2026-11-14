# AgroSmart — AI-Based Soil Analysis & Precision Crop Recommendation System

> **B.Tech Artificial Intelligence & Machine Learning — Minor Project Finalization**
> **Status:** Academic Submission Ready · 143/143 Pytest Tests Passing · Clean Production Build

---

## 1. Project Overview

**AgroSmart** is an intelligent, multi-modal agricultural decision-support platform designed to empower smallholder and commercial farmers with data-driven agronomic insights. By bridging computer vision and tabular machine learning, AgroSmart synthesizes visual soil surface photography with physical soil-environmental telemetry to deliver synchronized crop selection, targeted fertilizer planning, and adaptive irrigation scheduling.

### Academic Implementation & Software Simulation Disclosure
* **Software-Only Architecture:** AgroSmart operates as a fully functional, self-contained software platform. In this academic minor project prototype, environmental sensor telemetry is ingested through a **deterministic hardware simulation engine** (`SENSOR_MODE=simulator`) or via **manual 9-parameter soil data entry** (`POST /api/analysis/run` and `POST /api/sensors/reading`).
* **Conceptual Hardware Blueprint:** Hardware schematics, wiring pinouts, and driver architectures for physical sensors (DHT22 air sensor, DS18B20 soil temperature probe, capacitive moisture sensor, analog pH probe, RS-485 Modbus NPK sensor, and Raspberry Pi 5) are detailed in [`docs/hardware-setup.md`](docs/hardware-setup.md). Physical hardware is **not required** to run, evaluate, or verify this software system.

---

## 2. Problem Statement

Modern agriculture faces critical productivity and sustainability challenges:

1. **Delayed Soil Testing Turnaround:** Conventional laboratory soil testing typically requires **15 to 30 days** from sample collection to report delivery, creating severe decision latency during crucial pre-sowing planting windows.
2. **Empirical and Imbalanced Fertilizer Application:** Over-reliance on blanket chemical fertilizers (such as excessive Urea) leads to soil acidification, nutrient imbalance ($NPK$), groundwater nitrate leaching, and unnecessary input costs.
3. **Inefficient Water Management:** Fixed-interval flood irrigation wastes scarce groundwater reserves and exacerbates root asphyxiation, lacking responsiveness to ambient evaporative demand and soil moisture thresholds.
4. **Disjointed Decision Tools:** Existing agricultural tools treat soil visual texture, laboratory chemistry, and weather telemetry as isolated data silos rather than an integrated agronomic system.

AgroSmart resolves these challenges by providing an **instant, multi-modal decision platform** that combines visual soil classification, real-time telemetry assessment, predictive crop matching, targeted fertilizer diagnostics, and evapotranspiration-based irrigation advice in a single unified interface.

---

## 3. Core Features

* **Real-Time Telemetry Dashboard:** Interactive monitoring of **9 core soil-environmental parameters** (Nitrogen, Phosphorus, Potassium, pH, Moisture, Rainfall, Soil Temperature, Air Temperature, Air Humidity) with visual trend gauges and out-of-bound warnings.
* **Computer Vision Soil Classification:** Automated visual soil texture identification (Alluvial, Black, Clay, Red) powered by a fine-tuned MobileNetV2 Deep Convolutional Neural Network.
* **Multi-Class Precision Crop Recommendation:** High-accuracy matching across **22 distinct crop varieties** using an optimized Random Forest ensemble with probability-ranked recommendations.
* **Targeted Fertilizer Planning:** Diagnostic formulation guidance (7 NPK formulations) based on multi-parameter soil nutrient deficiencies with built-in Alluvial texture safeguards.
* **Smart Irrigation Scheduling:** Evapotranspiration-based moisture replenishment engine derived from FAO-56 Penman-Monteith principles and soil water-holding capacities.
* **Unified Historical Records:** Centralized historical logging with paginated search across telemetry snapshots, soil analyses, and AI recommendations.
* **Resilient Defensive Architecture:** Global React error boundaries, defensive backend payload normalization, and safe fallback cascades for edge-case soil textures.

---

## 4. Technology Stack

### Backend Infrastructure
* **Runtime & Language:** Python 3.12
* **Web Framework:** Flask 2.3+ (Application Factory pattern, Modular Blueprints, CORS enabled)
* **Database & ORM:** SQLite 3 with SQLAlchemy 2.0+ and Flask-Migrate (Alembic)
* **Hardware Abstraction Layer (HAL):** Deterministic software simulation with Raspberry Pi 5 GPIO drivers

### Machine Learning & Data Science
* **Deep Learning Framework:** TensorFlow / Keras 2.18 (MobileNetV2 Transfer Learning)
* **Tabular ML Algorithms:** Scikit-Learn 1.5+ (Random Forest Classifier, Decision Tree Classifier)
* **Data Processing & Deduplication:** NumPy, Pandas, Pillow, and Perceptual Difference Hashing (dHash)

### Frontend Dashboard
* **UI Framework:** React 18.2 with Functional Components and Custom Hooks
* **Build Tooling:** Vite 5.4 (ultra-fast Hot Module Replacement & production bundling)
* **Styling & Icons:** Tailwind CSS 3.4 with Lucide React icons
* **HTTP Client:** Centralized Axios instance with defensive error extraction

---

## 5. System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        REACT 18 WEB DASHBOARD                          │
│   (Dashboard · Soil Analysis · Crop Rec · Fertilizer · Irrigation)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST (Vite Proxy :5000)
┌───────────────────────────────────▼────────────────────────────────────┐
│                       FLASK REST API BACKEND                           │
│  ┌─────────────────┬───────────────────┬────────────────────────────┐  │
│  │ /api/health     │ /api/sensors/*    │ /api/analysis/*            │  │
│  │ /api/images/*   │ /api/predictions/*│ Global Error Handler       │  │
│  └────────┬────────┴─────────┬─────────┴─────────────┬──────────────┘  │
│           │                  │                       │                 │
│  ┌────────▼────────┐┌────────▼────────┐┌─────────────▼──────────────┐  │
│  │ HARDWARE LAYER  ││ DATABASE (ORM)  ││   AI / ML INFERENCE ENGINE  │  │
│  │ Simulated HAL   ││ SQLite 3        ││ MobileNetV2 (Soil CNN)      │  │
│  │ (Raspberry Pi   ││ SensorReading   ││ Random Forest (Crop Rec)    │  │
│  │  Blueprint)     ││ SoilAnalysis    ││ Decision Tree (Fertilizer)  │  │
│  │                 ││ Prediction      ││ FAO-56 Rule Engine (Water)  │  │
│  └─────────────────┘└─────────────────┘└────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

Detailed architectural diagrams are available in [`docs/uml_diagrams/simplified/`](docs/uml_diagrams/simplified/):
* **Component Diagram:** [`docs/uml_diagrams/simplified/component_diagram.png`](docs/uml_diagrams/simplified/component_diagram.png)
* **Class Diagram:** [`docs/uml_diagrams/simplified/class_diagram.png`](docs/uml_diagrams/simplified/class_diagram.png)
* **Sequence Diagram:** [`docs/uml_diagrams/simplified/sequence_diagram.png`](docs/uml_diagrams/simplified/sequence_diagram.png)
* **Use Case Diagram:** [`docs/uml_diagrams/simplified/use_case_diagram.png`](docs/uml_diagrams/simplified/use_case_diagram.png)

---

## 6. Project Visualizations & Evaluation Charts

High-resolution performance visualizations and evaluation curves are bundled in `docs/`:

* **Crop Random Forest Evaluation:**
  Confusion matrix, ROC curves, and feature importance rankings: [`docs/model_evaluation/crop_rf_evaluation.png`](docs/model_evaluation/crop_rf_evaluation.png)
* **Soil CNN Performance & Accuracy:**
  Training loss, validation accuracy curves, and per-class precision: [`docs/model_evaluation/soil_cnn_evaluation.png`](docs/model_evaluation/soil_cnn_evaluation.png)
* **Fertilizer Decision Tree Metrics:**
  Decision tree depth analysis and multi-class confusion matrix: [`docs/model_evaluation/fertilizer_dt_evaluation.png`](docs/model_evaluation/fertilizer_dt_evaluation.png)
* **Model Comparison Summary:**
  Cross-model performance metrics and latency breakdown: [`docs/model_evaluation/model_comparison_summary.png`](docs/model_evaluation/model_comparison_summary.png)

---

## 7. Quick Start & Execution Instructions

### Prerequisites
* **Python:** 3.11 or 3.12 installed on system path
* **Node.js:** 18.x or 20.x LTS with `npm`
* **Git:** Installed on system path

Pre-trained model weights are bundled in `backend/trained_models/`. **No model retraining or dataset download is required to run the application.**

---

### Step A: Backend Setup & Execution

```bash
# 1. Clone the repository
git clone https://github.com/<username>/agrosmart.git
cd agrosmart

# 2. Navigate to the backend directory
cd backend

# 3. Create and activate a Python virtual environment
# Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate

# 4. Install backend dependencies
pip install -r requirements.txt

# 5. Configure environment variables
# Copy the provided template (preconfigured for simulator mode)
cp .env.example .env

# 6. Start the Flask API server
python run.py
```
* The Flask backend will start on **`http://localhost:5000`**.
* Verify API health by navigating to: `http://localhost:5000/api/health`

---

### Step B: Frontend Setup & Execution

Open a separate terminal window:

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install Node.js packages
npm install

# 3. Start the Vite development server
npm run dev
```
* The React dashboard will be live at: **`http://localhost:3000`** (or `http://localhost:5173`).
* In development mode, Vite automatically proxies API requests (`/api/*`) to `http://localhost:5000`.

---

### Step C: Production Frontend Build

To verify production bundling:
```bash
cd frontend
npm run build
```
This generates a minified, standalone static bundle in `frontend/dist/`.

---

## 8. Machine Learning Models & Academic Limitations

| Model Pillar | Algorithm / Architecture | Input Dimension | Target Classes | Evaluation Metric | Status & Scope |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Soil Classification** | MobileNetV2 (Transfer Learning) | $224 \times 224 \times 3$ RGB | 4 soil classes | **81.69% accuracy** on 71 clean test images | **Production (V1)** |
| **Crop Recommendation** | Random Forest (100 trees) | 7 environmental features | 22 agricultural crops | **99.09% accuracy** on 440 test samples | **Production (V1)** |
| **Fertilizer Advisory** | Decision Tree Classifier | 8 soil/crop parameters | 7 NPK formulations | Academic baseline | **Prototype (Kaggle)** |
| **Irrigation Scheduling** | FAO-56 Penman-Monteith Rule Engine | Moisture, Temp, Humidity, Texture | 4 schedule urgency tiers | Agronomic rule-based | **Deterministic Engine** |

### Academic Scope & Model Limitations:
1. **Soil Classification (MobileNetV2):** Operates on surface soil photography. While highly effective at distinguishing distinct chromas and coarseness (Red vs. Black vs. Clay), it cannot infer internal subsurface chemical composition without telemetry.
2. **Fertilizer Advice Prototype:** The Decision Tree fertilizer model is trained on a synthetic Kaggle benchmark dataset and serves as an academic proof-of-concept. For production deployments, it must be retrained against regional soil testing data from bodies like ICAR or Krishi Vigyan Kendras.
3. **Texture Safeguard:** The fertilizer prototype dataset lacks native Alluvial soil training samples; AgroSmart implements an automated safe-fallback handler that substitutes validated Loam/Sandy-Loam nutrient profiles.

---

## 9. Automated Testing & Verification Suite

All application subsystems are verified through automated unit, integration, smoke, and end-to-end tests:

### 1. Pytest Backend Suite (143 Tests)
```bash
cd backend
python -m pytest tests/ -v
```
* **Result:** **143 passed in 32.22s (100% pass rate · 0 failures · 0 skipped)**
  * `tests/test_api.py` (80 tests): Comprehensive coverage of REST endpoints, validation boundaries, and error rollback.
  * `tests/test_ml_pipeline.py` (40 tests): ML inference wrappers, Alluvial texture safeguards, and irrigation logic.
  * `tests/test_simulator.py` (7 tests): HAL simulation, sensor bounds checking, and cache freshness.
  * `tests/test_soil_cnn_evaluation.py` (9 tests): Clean dataset manifest integrity, split isolation, and zero-leakage verification.
  * `tests/test_soil_cnn_v2.py` (7 tests): V2 ablation architecture tests and V1 baseline immutability.

### 2. In-Process Smoke Verification (6 Endpoints)
```bash
cd backend
python smoke_test.py
```
* **Result:** **6/6 passed** (`/api/health`, `/api/sensors/latest`, `/api/analysis/run`, `/api/sensors/history`, `/api/analysis/history`, `/api/predictions/latest`).

### 3. End-to-End Workflow Verification (4 User Journeys)
```bash
cd backend
python test_e2e_workflows.py
```
* **Result:** **4/4 passed** (Pure Manual 8/9-Param Analysis, Image Upload & CNN Inference, Alluvial Texture Safeguard, Boundary Validation).

### 4. Frontend Production Build
```bash
cd frontend
npm run build
```
* **Result:** Built cleanly in 8.77s with Vite (0 errors, 0 compilation warnings).

---

## 10. REST API Reference

The backend provides a complete RESTful API interface:

| Method | Endpoint | Description | Primary Query / Payload Parameters |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | System health, database status, sensor mode | None |
| `GET` | `/api/sensors/latest` | Retrieve current 9-parameter reading | None |
| `POST`| `/api/sensors/reading`| Ingest new sensor telemetry reading | `nitrogen`, `phosphorus`, `potassium`, `ph`, `moisture`, `temperature`, `humidity` |
| `GET` | `/api/sensors/history`| Paginated historical sensor telemetry | `page`, `per_page` |
| `POST`| `/api/analysis/run` | Run complete unified AI analysis | `reading_id` OR `sensor_data` (9 parameters), `soil_type`, `confirmed_soil_texture`, `image_path` |
| `GET` | `/api/analysis/<id>` | Fetch single complete analysis by ID | Path parameter `id` |
| `GET` | `/api/analysis/history`| Paginated analysis history | `page`, `per_page` |
| `GET` | `/api/predictions/latest` | Latest crop, fertilizer, & irrigation results | None |
| `GET` | `/api/predictions/<id>` | Fetch single prediction record by ID | Path parameter `id` |
| `GET` | `/api/predictions/history`| Paginated prediction history | `page`, `per_page`, `prediction_type` |
| `POST`| `/api/images/upload` | Upload soil photo for CNN classification | `multipart/form-data` with `image` file; optional `run_analysis=true` |
| `GET` | `/api/images/<filename>`| Serve uploaded soil image | Path parameter `filename` |

Full schema specifications, JSON request bodies, and error response contracts are documented in [`docs/api-reference.md`](docs/api-reference.md).

---

## 11. Future Scope & Roadmap

For major project expansion and commercial deployment, the following enhancements are planned:

1. **Physical Edge Deployment:** Deploying the backend onto Raspberry Pi 5 hardware using the verified schematics in `docs/hardware-setup.md` with IP67 weatherproof field enclosures.
2. **Edge AI Acceleration:** Quantizing the MobileNetV2 CNN to TensorFlow Lite (TFLite) for sub-50ms inference on Google Coral USB TPU accelerators.
3. **Regional Agronomic Datasets:** Replacing the Kaggle fertilizer prototype with verified regional soil health card datasets from the Indian Council of Agricultural Research (ICAR).
4. **LoRaWAN / Satellite Telemetry:** Integrating long-range, low-power telemetry transmission (LoRaWAN 868/915 MHz) for connectivity across remote rural fields.
5. **Multilingual Mobile Interface:** Developing a localized Flutter mobile application with vernacular voice-guided interfaces in regional Indian languages (Hindi, Marathi, Punjabi, Telugu).

---

## 12. Academic Project Information & Contributors

* **Degree:** Bachelor of Technology (B.Tech) in Artificial Intelligence & Machine Learning
* **Course:** Minor Project Finalization
* **Project Title:** AgroSmart: AI-Based Soil Analysis & Precision Crop Recommendation System
* **Academic Year:** 2026–2027
* **Submission Date:** November 2026

### Project Contributors
| Contributor Name | Role | Department | Institution |
| :--- | :--- | :--- | :--- |
| **Dharmendra Meena** | Lead Developer & ML Architect | AI & Machine Learning | Department of Computer Science & Engineering |
| *(Project Partner)* | Frontend Developer / Data Analyst | AI & Machine Learning | Department of Computer Science & Engineering |

### Project Supervision
* **Project Guide:** *(Faculty Guide Name)*, Assistant Professor / Associate Professor
* **Department:** Department of Computer Science & Engineering (AI & ML)
* **Institution:** *(College / University Name)*

---

## 13. Documentation Directory Index

* **[`docs/finalization/minor_project_report.md`](docs/finalization/minor_project_report.md):** Complete academic minor project report with theoretical foundations, system design, and results.
* **[`docs/finalization/viva_defense_guide.md`](docs/finalization/viva_defense_guide.md):** 40-question comprehensive Viva Voce defense preparation guide.
* **[`docs/finalization/presentation_content.md`](docs/finalization/presentation_content.md):** Approved 15-slide presentation script.
* **[`docs/finalization/AgroSmart_Minor_Project_Presentation.pptx`](docs/finalization/AgroSmart_Minor_Project_Presentation.pptx):** Final 15-slide PowerPoint deck.
* **[`docs/api-reference.md`](docs/api-reference.md):** Complete REST API specification with sample payloads and status codes.
* **[`docs/ml-pipeline.md`](docs/ml-pipeline.md):** Detailed ML methodology, perceptual deduplication audit, and performance metrics.
* **[`docs/hardware-setup.md`](docs/hardware-setup.md):** Conceptual hardware blueprints, pinout schematics, and sensor specifications.
* **[`docs/finalization/github_readiness_audit.md`](docs/finalization/github_readiness_audit.md):** Forensic GitHub repository readiness audit.

---

## 14. License

This project is open-source software licensed under the **[MIT License](LICENSE)**.

```
Copyright (c) 2026 Dharmendra Meena and AgroSmart Project Contributors
```
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files to use, copy, modify, merge, publish, and distribute without restriction, subject to the conditions in the [`LICENSE`](LICENSE) file.
