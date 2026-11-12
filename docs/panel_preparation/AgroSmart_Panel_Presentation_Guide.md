# AgroSmart — Panel Presentation Guide (Slide-by-Slide)
**B.Tech Minor Project Panel 2 Evaluation Reference Manual**
**System Title:** AgroSmart — AI-Based Soil Analysis & Crop Recommendation System  
**Repository Location:** `D:\minor 1\Agrosmart`  
**Team Members:**
- Dharmendra Meena (241B616)
- Mayur Kushwah (241B623)
- Shivani Yadav (241B315)

---

## 1. Work Plan & Status Summary

| Work Package | Deliverables & Artifacts | Status | Evidence / Verification Files |
| :--- | :--- | :---: | :--- |
| **WP 1: Problem Definition & Architecture** | Requirement specifications, modular software plan, HAL interface | **Completed** | [`agrosmart-architecture-plan.md`](file:///D:/minor%201/agrosmart-architecture-plan.md) |
| **WP 2: Backend Architecture & REST APIs** | Flask 3.x factory, 5 Blueprints, SQLite ORM models, validation | **Completed** | [`backend/app/`](file:///D:/minor%201/Agrosmart/backend/app/), 111 backend pytest tests passing |
| **WP 3: Tabular ML Inference Wrappers** | Crop Random Forest (22 crops), Fertilizer Decision Tree (Prototype) | **Completed** | [`backend/app/ml/crop_model.py`](file:///D:/minor%201/Agrosmart/backend/app/ml/crop_model.py), [`fertilizer_model.py`](file:///D:/minor%201/Agrosmart/backend/app/ml/fertilizer_model.py) |
| **WP 4: Computer Vision Soil Classification** | 671 image dataset deduplication, MobileNetV2 CNN transfer learning | **Completed** | **90.10% Test Acc** ([`soil_cnn_metrics.json`](file:///D:/minor%201/Agrosmart/backend/trained_models/soil_cnn_metrics.json)) |
| **WP 5: Agronomic Advisory Rule Engines** | Soil health scoring (0-100), drainage-adjusted irrigation advice | **Completed** | [`backend/app/services/recommendation_service.py`](file:///D:/minor%201/Agrosmart/backend/app/services/recommendation_service.py) |
| **WP 6: Frontend Integration & Dashboard** | React 18 SPA, Vite build, Tailwind UI, Zustand store, history table | **Completed** | [`frontend/src/`](file:///D:/minor%201/Agrosmart/frontend/src/), Vite production build passing in 9.9s |
| **WP 7: End-to-End Pipeline & Safeguards** | Alluvial texture confirmation, rainfall vs moisture separation | **Completed** | [`backend/test_e2e_workflows.py`](file:///D:/minor%201/Agrosmart/backend/test_e2e_workflows.py) (4/4 workflows verified) |
| **WP 8: Physical Hardware Integration** | Raspberry Pi 5, MCP3008 ADC, RS485 NPK probe, Pi Camera | *Planned (Phase 5)* | Code scaffolded in [`backend/app/hardware/raspberry_pi.py`](file:///D:/minor%201/Agrosmart/backend/app/hardware/raspberry_pi.py) |

---

## 2. Individual Contribution Division

*Note for Evaluation Panel: All three members participated collaboratively in system architecture and testing. The primary individual module ownership is distributed as follows:*

| Student Name & Roll No. | Primary Module Ownership | Core Technical Contributions |
| :--- | :--- | :--- |
| **Dharmendra Meena**<br>(241B616) | **Machine Learning & Computer Vision** | • Dataset curation, deduplication, and cryptographic hash audit for 671 soil images.<br>• MobileNetV2 transfer learning architecture, two-stage fine-tuning, and evaluation on held-out test split (90.10% test accuracy).<br>• Random Forest crop recommendation inference pipeline. |
| **Mayur Kushwah**<br>(241B623) | **Backend Architecture & System Pipeline** | • Flask 3.x REST API gateway, blueprint architecture, and error handling.<br>• SQLite database schema design and SQLAlchemy ORM models (`SensorReading`, `SoilAnalysis`, `Prediction`).<br>• Hardware Abstraction Layer (HAL) and sinusoidal drift simulation engine. |
| **Shivani Yadav**<br>(241B315) | **Frontend Engineering & System Integration** | • React 18 Single-Page Application (SPA) development with Vite and Tailwind CSS.<br>• Interactive parameter workstation, preset selectors, and soil image upload widget.<br>• Zustand global state management, Axios API client, and paginated historical analysis view. |

---

## 3. Slide-by-Slide Presentation Content

### Slide 1: Title Slide & Project Identification
- **Title:** AgroSmart: AI-Based Soil Analysis & Crop Recommendation System
- **Subtitle:** B.Tech Minor Project — Phase 2 Evaluation
- **Team Details:**
  - Dharmendra Meena (241B616)
  - Mayur Kushwah (241B623)
  - Shivani Yadav (241B315)
- **Institution:** Department of Computer Science & Engineering
- **Key Points:**
  - Full-stack AI agricultural workstation combining computer vision, ensemble machine learning, and rule-based agronomy.
  - Developed and verified in standalone software simulation mode.
- **Speaker Notes:** *"Good morning respected evaluators. Today our team presents AgroSmart, an intelligent decision-support system designed to replace slow, expensive soil testing with instant multi-modal AI analysis."*

---

### Slide 2: Problem Statement
- **Slide Title:** The Challenges in Smallholder Soil Management
- **Key Points:**
  - **Testing Latency:** Conventional wet-chemistry soil labs take 2–4 weeks; farmers sow crops before results arrive.
  - **Subjective Heuristics:** Visual soil inspection cannot quantify macronutrients (N, P, K) or pH.
  - **Imbalanced Chemical Fertilization:** Blanket application of Urea and DAP leads to soil acidification, water table contamination, and yield loss.
  - **Climate Sensitivity:** Lack of localized irrigation planning leads to water wastage or crop desiccation.
- **Visual Suggestion:** Side-by-side comparison table: Conventional Lab Testing vs. AgroSmart Decision Support.
- **Speaker Notes:** *"Traditional soil testing is inaccessible to most smallholder farmers due to delay and cost. Without data, farmers apply blanket fertilizers, damaging soil ecology. AgroSmart provides an objective, immediate alternative."*

---

### Slide 3: Literature Review & Existing Systems
- **Slide Title:** Background & Comparative Study
- **Key Points:**
  - **P. S. et al. (2020):** Crop recommendation using machine learning on soil nutrients (validated Random Forest as top classifier for agricultural tabular data).
  - **Sandler et al. (2018):** MobileNetV2 architecture (inverted residuals and depthwise convolutions achieve 90%+ image classification on low-power devices).
  - **Existing Agricultural Portals:** Static regional lookup tables without sensor integration or image analysis.
  - **AgroSmart Advancement:** Multi-modal fusion—combining photographic soil order classification (CNN), multi-class crop ranking (RF), safeguarded fertilizer advice (DT), and dynamic moisture rules.
- **Speaker Notes:** *"Prior literature either examines tabular crop prediction or agricultural image classification in isolation. AgroSmart fuses both into a unified software pipeline."*

---

### Slide 4: Work Plan & Methodology
- **Slide Title:** Engineering Methodology & Project Phases
- **Key Points:**
  - **Phased Approach:**
    - *Phase 1:* Tabular model training, crop mapping audit, and scientific withholding.
    - *Phase 2:* Soil image dataset audit (671 deduplicated images), MobileNetV2 two-stage training, and evaluation.
    - *Phase 3:* End-to-end software analysis pipeline with parameter separation (rainfall vs. moisture) and Alluvial safeguards.
    - *Phase 4:* React frontend integration, presets, history archive, and system testing.
    - *Phase 5 (Planned):* Physical Raspberry Pi 5 hardware integration and field calibration.
- **Visual Suggestion:** Phased timeline flowchart from Phase 1 through Phase 5.
- **Speaker Notes:** *"We followed a strict modular roadmap. Rather than waiting for physical hardware, we built a fully functional software simulation workstation with verified models and automated tests."*

---

### Slide 5: System Architecture & Workflow (UML)
- **Slide Title:** AgroSmart System Architecture & Runtime Workflow
- **Key Points:**
  - **Four-Tier Architecture:** Client Tier (React 18 SPA) $\rightarrow$ Application Tier (Flask 3.x REST API) $\rightarrow$ Intelligence Tier (MobileNetV2, Random Forest, Decision Tree) $\rightarrow$ Persistence Tier (SQLite + SQLAlchemy).
  - **Hardware Abstraction Layer (HAL):** Isolates GPIO; operates in software simulation mode with realistic sinusoidal parameter drift.
  - **Workflow:** 11-step request lifecycle from user parameter entry to database transaction and JSON presentation.
- **Visual Suggestion:** Embed [`docs/uml_diagrams/simplified/component_diagram.png`](file:///D:/minor%201/Agrosmart/docs/uml_diagrams/simplified/component_diagram.png) and [`sequence_diagram.png`](file:///D:/minor%201/Agrosmart/docs/uml_diagrams/simplified/sequence_diagram.png).
- **Speaker Notes:** *"Our architecture cleanly separates presentation, business orchestration, and persistence. The HAL enables standalone software execution while remaining ready for physical sensors."*

---

### Slide 6: Machine Learning Models & Soil CNN Results
- **Slide Title:** AI/ML Models & Verified CNN Evaluation Evidence
- **Key Points:**
  - **Soil Image CNN (MobileNetV2):**
    - 671 images across 4 classes: Alluvial, Black, Clay, Red (70/15/15 stratified split, 0 hash leakage).
    - **90.10% Test Accuracy (0.9010), Test Loss: 0.3692** on held-out 101-image test set.
    - Red soil: 100% recall; Alluvial soil: 95.3% recall.
  - **Crop Recommendation (Random Forest):** 100 trees, 7 input features, 22 output crops with top-3 probabilistic ranking.
  - **Fertilizer Recommendation (Decision Tree):** Prototype model with scientific crop mapping and Alluvial texture confirmation safeguard.
- **Visual Suggestion:** Confusion matrix table and training/validation loss curves.
- **Speaker Notes:** *"Our soil image classifier achieved 90.1% accuracy on the held-out test split using transfer learning with frozen batch normalization layers to prevent overfitting."*

---

### Slide 7: Agronomic Rule Engines & Diagnostics
- **Slide Title:** Soil Health Scoring & Irrigation Advisory Engines
- **Key Points:**
  - **Composite Soil Health Index (0–100):**
    - Evaluates pH (25 pts), Moisture (25 pts), NPK sufficiency (25 pts), and Temperature (25 pts).
    - Status classifications: Good ($\ge 70$), Fair ($45\text{--}69$), Poor ($< 45$).
  - **Irrigation Advisory Engine:**
    - Calculates *Effective Moisture* by applying soil drainage modifiers (Clay $+8\%$, Sandy $-8\%$) and crop water tiers (High $+5\%$, Low $-5\%$).
    - Outputs recommended action, urgency, frequency, and estimated water volume ($L/m^2$).
    - Thermal evapotranspiration advisory triggered when air temperature $> 38^\circ\text{C}$.
- **Speaker Notes:** *"In addition to ML classifiers, AgroSmart implements deterministic agronomic logic to calculate a soil health score and generate tailored irrigation schedules."*

---

### Slide 8: Software Workstation & User Interface
- **Slide Title:** React 18 Analysis Workstation Demonstration
- **Key Points:**
  - **Live Telemetry Dashboard:** Visualizes simulated environmental sensors with automated polling and Recharts trend lines.
  - **Manual Workstation:** 8-parameter manual input form with agricultural presets and soil photo upload widget.
  - **Historical Archive:** Searchable, paginated audit log retrieving past analyses and predictions from SQLite.
  - **Production Quality:** Production build verified with Vite (0 errors in 9.9 seconds); 111 backend pytest tests passing.
- **Visual Suggestion:** Actual application screenshot of the Soil Analysis results card.
- **Speaker Notes:** *"Here is our React frontend workstation. Users can enter soil values manually or rely on the simulator, upload an image, and view results with diagnostic confidence bars."*

---

### Slide 9: Work to Be Done (Phase 5 Hardware & Field Validation)
- **Slide Title:** Future Scope & Hardware Integration Roadmap
- **Key Points:**
  - **Physical Sensor Wiring (Phase 5):** Connecting Raspberry Pi 5 with MCP3008 ADC (capacitive moisture, analog pH), DS18B20 1-Wire temperature, and RS485 UART NPK probe.
  - **Field Calibration:** Retraining the prototype fertilizer model with empirically collected farm soil samples.
  - **Model Generalization:** Expanding soil image dataset across diverse moisture states and lighting conditions.
  - **Progressive Web App (PWA):** Adding offline caching for remote field operation.
- **Speaker Notes:** *"The next phase of our project focuses on physical hardware integration with Raspberry Pi 5 sensors and empirical field testing with local farmers."*

---

### Slide 10: Conclusion & References
- **Slide Title:** Summary & References
- **Key Points:**
  - Delivered a robust, verified, full-stack precision agriculture workstation.
  - Verified 90.10% accuracy on soil classification and integrated multi-model advisory pipelines.
  - Prioritized engineering integrity: scientific withholding, separate rainfall/moisture features, and explicit labeling of simulated vs. hardware modes.
- **References (IEEE Format):**
  1. P. S. et al., "Crop Recommendation System using Machine Learning," *IEEE International Conference on Inventive Computation Technologies (ICICT)*, 2020.
  2. M. Sandler et al., "MobileNetV2: Inverted Residuals and Linear Bottlenecks," *IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, 2018.
  3. F. Pedregosa et al., "Scikit-learn: Machine Learning in Python," *Journal of Machine Learning Research (JMLR)*, vol. 12, pp. 2825-2830, 2011.
- **Speaker Notes:** *"Thank you. AgroSmart proves that software-driven precision agriculture can provide fast, accessible, and scientifically sound decision support. We welcome questions from the evaluation panel."*
