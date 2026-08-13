# AgroSmart — ML Pipeline Guide

## Overview

AgroSmart uses three ML/AI models and one rule engine:

| Model | Type | File | Dataset | Status |
|-------|------|------|---------|--------|
| Crop Recommendation | Random Forest | `crop_rf_v1.pkl` | Kaggle (2200 rows) | ✅ Trained |
| Fertilizer Recommendation | Decision Tree | `fertilizer_dt_prototype.pkl` | Kaggle ⚠ Prototype | ✅ Trained |
| Soil Classification | CNN MobileNetV2 | `soil_cnn_v1.h5` | Soil image dataset | ⏳ Requires images |
| Irrigation Advice | Rule engine | (no file) | — | ✅ Active |

---

## 1. Crop Recommendation — Random Forest

### Input features (7)
| Feature | Source | Units |
|---------|--------|-------|
| nitrogen | NPK sensor | mg/kg |
| phosphorus | NPK sensor | mg/kg |
| potassium | NPK sensor | mg/kg |
| temperature | DS18B20 (soil) | °C |
| humidity | DHT22 (air) | % |
| ph | pH sensor | 0–14 |
| rainfall | moisture sensor (proxy) | % |

> The Kaggle dataset uses `rainfall` (mm/year). At inference time, soil moisture % is
> used as a proxy. When real rainfall data is available (weather API, Phase 6+),
> replace the moisture value with actual rainfall.

### Output
Top-N crops (default 3) with class probability scores.

### Training

```bash
# Place CSV at ml_training/datasets/crop_recommendation.csv
# (Kaggle: https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset)
# OR generate synthetic data for testing:
python ml_training/generate_synthetic_datasets.py

# Train
python ml_training/train_crop_model.py
# Output: trained_models/crop_rf_v1.pkl
#         trained_models/crop_scaler.pkl
```

### Evaluation
```bash
python ml_training/evaluate_models.py --model crop
```
Reports: test accuracy, CV-5 accuracy ± std, per-class F1, feature importances.

### Retraining with AgroSmart data (Phase 5+)
1. Collect real readings with confirmed crop outcomes in the field.
2. Save as CSV matching the Kaggle schema (N, P, K, temperature, humidity, ph, rainfall, label).
3. Re-run `train_crop_model.py` → saves `crop_rf_v2.pkl`.
4. Update `CROP_MODEL_PATH=trained_models/crop_rf_v2.pkl` in `.env`.

---

## 2. Fertilizer Recommendation — Decision Tree (Prototype)

> ⚠ **Prototype model** — trained on Kaggle data. Replace with AgroSmart-collected
> data before final project submission (run with `--final` flag).

### Input features (8)
| Feature | Source |
|---------|--------|
| temperature | air_temperature (DHT22) |
| humidity | air_humidity (DHT22) |
| moisture | moisture sensor |
| soil_type | CNN output or heuristic |
| crop_type | top crop recommendation |
| nitrogen | NPK sensor |
| potassium | NPK sensor |
| phosphorus | NPK sensor |

### Output classes
Urea, DAP, 14-35-14, 28-28, 17-17-17, 20-20, 10-26-26

### Training — Prototype
```bash
# Place CSV at ml_training/datasets/fertilizer_recommendation.csv
# (Kaggle: https://www.kaggle.com/datasets/gdabhishek/fertilizer-prediction)

python ml_training/train_fertilizer_model.py
# Output: trained_models/fertilizer_dt_prototype.pkl  [labelled as prototype]
```

### Training — Final (AgroSmart data)
```bash
# Replace with your real AgroSmart sensor + field data CSV
python ml_training/train_fertilizer_model.py --final
# Output: trained_models/fertilizer_dt_final.pkl
```

Then update `.env`:
```ini
FERTILIZER_MODEL_PATH=trained_models/fertilizer_dt_final.pkl
FERTILIZER_MODEL_LABEL=final_agrosmart_v1.0
```

### Model label tracking
Every prediction record in the DB stores `model_version`. This lets you
compare prototype vs. final model performance over time in the History page.

---

## 3. Soil Image Classification — CNN (MobileNetV2)

### Architecture
- **Base:** MobileNetV2 pretrained on ImageNet (frozen in phase 1)
- **Head:** GlobalAveragePooling2D → Dropout(0.3) → Dense(128) → Dropout(0.2) → Dense(N, softmax)
- **Input size:** 224×224×3, normalised to [0, 1]
- **Training:** 2-phase (freeze base → fine-tune top 20 layers)

### Classes
Sandy, Clay, Loamy, Silty  (add more by extending the image dataset)

### Dataset preparation
```
ml_training/datasets/soil_images/
    Sandy/        ← at least 100 images each
    Clay/
    Loamy/
    Silty/
```

Recommended source: search Kaggle for **"Soil Type Classification"** or
**"Soil Image Dataset"**. At least 100 images per class for acceptable accuracy.

### Training
```bash
# Requires TensorFlow
pip install tensorflow opencv-python-headless Pillow

python ml_training/train_soil_cnn.py
# Output: trained_models/soil_cnn_v1.h5
#         trained_models/soil_cnn_classes.pkl
```

### Graceful degradation
If TensorFlow is not installed or the model file is absent, `soil_cnn.py` returns:
```json
{ "soil_type": null, "confidence": null, "cnn_status": "model_unavailable" }
```
The analysis pipeline continues using the sensor-based heuristic soil type.

### Research note
As documented in the AgroSmart research summary, soil surface roughness
significantly affects optical reflectance (up to 44–60% deviation in SWIR2).
For best CNN accuracy: capture images **close-range** (< 30 cm), **consistent
overhead lighting**, and **undisturbed soil surface**.

---

## 4. Irrigation Advice — Rule Engine

No model file. Pure Python logic in `services/recommendation_service.py`.

### Decision logic
```
effective_moisture = raw_moisture + soil_type_modifier - crop_demand_modifier

< 25%  → critical  : Irrigate immediately
< 40%  → high      : Irrigate within 24 hours
< 60%  → medium    : Monitor (every 2–3 days)
< 75%  → low       : No irrigation (check in 3–4 days)
≥ 75%  → none      : Well saturated (check in 5–7 days)
```

### Soil type modifiers (% offset)
Sandy: −8 | Loamy: 0 | Silty: +3 | Clay: +8

### Crop water demand tiers
High (rice, banana, sugarcane): +5% demand
Low (chickpea, lentil, blackgram): −5% demand
Medium (wheat, maize, cotton): 0%

### Adjusting thresholds
Edit the constants at the top of `recommendation_service.py`:
```python
CRITICAL_LOW = 25.0
LOW          = 40.0
ADEQUATE     = 60.0
HIGH         = 75.0
```

---

## 5. Preprocessing Pipeline

### Inference-time preprocessing (`app/ml/preprocessor.py`)
- Loads fitted scalers and encoders from `trained_models/`
- Maps sensor dict keys to correct feature column order
- Replaces `None` values with training-set median fallbacks
- No re-fitting at inference time

### Fallback medians (used when sensors return NULL)
| Feature | Median fallback |
|---------|----------------|
| nitrogen | 40.0 mg/kg |
| phosphorus | 25.0 mg/kg |
| potassium | 180.0 mg/kg |
| ph | 6.5 |
| moisture | 52.0 % |
| temperature | 26.0 °C |
| humidity | 62.0 % |

Update these in `preprocessor.py` if retraining on a different dataset.

---

## 6. Model Versioning Policy

| Event | Action |
|-------|--------|
| Initial training | Save as `*_v1.pkl` |
| Retrain on AgroSmart data | Save as `*_v2.pkl`, update `config.py` |
| Switch prototype → final fertilizer model | Change `FERTILIZER_MODEL_PATH` in `.env` |
| Every prediction | `model_version` column in DB records which file was used |

To see which model produced a specific prediction:
```sql
SELECT id, prediction_type, model_version FROM predictions WHERE id = <id>;
```
