# AgroSmart — Machine Learning Pipeline & Model Evaluation Guide

**Project Phase:** Minor Project Finalization
**Document Version:** 2.0.0
**Updated:** November 2026

---

## 1. Executive Model Suite Summary

AgroSmart deploys an ensemble of multi-modal machine learning models and deterministic agronomic algorithms designed for agricultural decision support:

| Subsystem | Model Architecture | Saved Artifact | Input Features | Target Classes | Verified Test Performance | Production Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Crop Recommendation** | Random Forest Classifier (100 Trees) | `crop_rf_v1.pkl`<br>`crop_scaler.pkl` | 7 Tabular Features ($N, P, K, T, H, pH, R$) | 22 Crops | **99.09% Accuracy**<br>0.99 Macro F1 | **Active Production** |
| **Fertilizer Recommendation** | Decision Tree Classifier (Gini Impurity) | `fertilizer_dt_prototype.pkl`<br>`fertilizer_encoders.pkl`<br>`fertilizer_scaler.pkl` | 8 Features ($T, H, M, Soil, Crop, N, K, P$) | 7 Fertilizer Formulations | **98.90% Accuracy**<br>(With Alluvial Safeguard) | **Production Prototype** |
| **Soil Visual Classification (V1)** | MobileNetV2 CNN (Transfer Learning) | `soil_cnn_v1.h5`<br>`soil_cnn_classes.pkl` | $224 \times 224 \times 3$ RGB Image | 4 Pedological Classes (Alluvial, Black, Clay, Red) | **81.69% Accuracy**<br>81.62% Macro F1 | **Active Production** |
| **Comparative Soil CNN (V2)** | MobileNetV2 CNN (2-Stage Fine-Tuning) | `soil_cnn_v2.h5`<br>`soil_cnn_v2_classes.pkl` | $224 \times 224 \times 3$ RGB Image | 4 Pedological Classes (Alluvial, Black, Clay, Red) | **80.28% Accuracy**<br>80.48% Macro F1 | *Experimental Research Only* |
| **Smart Irrigation Advice** | Dynamic Rule Engine (FAO-56 Penman-Monteith) | Deterministic Code (`recommendation_service.py`) | Moisture, Air Temp, Humidity, Crop, Soil Texture | 5 Urgency Levels (Critical $\rightarrow$ None) | Deterministic Agronomic Logic | **Active Production** |

---

## 2. Crop Recommendation Model — Random Forest

### 2.1 Model Specifications
* **Architecture:** Scikit-Learn `RandomForestClassifier` with 100 decision trees, Gini impurity split criterion, bootstrap sampling enabled.
* **Input Features (7):**
  1. `N` (Nitrogen): $0$ to $140\ mg/kg$
  2. `P` (Phosphorus): $5$ to $145\ mg/kg$
  3. `K` (Potassium): $5$ to $205\ mg/kg$
  4. `temperature`: $8.0$ to $45.0\ ^\circ C$
  5. `humidity`: $14.0$ to $100.0\%$
  6. `ph`: $3.5$ to $10.0$
  7. `rainfall`: $20.0$ to $300.0\ mm$
* **Target Classes (22):** `apple`, `banana`, `blackgram`, `chickpea`, `coconut`, `coffee`, `cotton`, `grapes`, `jute`, `kidneybeans`, `lentil`, `maize`, `mango`, `mothbeans`, `mungbean`, `muskmelon`, `orange`, `papaya`, `pigeonpeas`, `pomegranate`, `rice`, `watermelon`.

### 2.2 Dataset Provenance & Empirical Evaluation
* **Source Dataset:** Kaggle Crop Recommendation Dataset (2,200 samples, 100 per crop class).
* **Evaluation Partition:** 80/20 stratified split (1,760 train samples, 440 test samples).
* **Evaluation Metrics:**
  * **Overall Accuracy:** **99.09%** (436 / 440 correct predictions).
  * **Macro Precision / Recall / F1:** **0.99 / 0.99 / 0.99**.
  * **5-Fold Cross Validation:** $99.27\% \pm 0.35\%$.
  * **Feature Importances:** Rainfall (22.8%), Humidity (21.4%), Potassium (17.6%), Phosphorus (14.2%), Nitrogen (10.5%), Temperature (7.8%), pH (5.7%).

> **Academic Disclosure on Real-World Generalization:**
> The 99.09% test accuracy reflects performance on a synthetic/benchmarking dataset with distinct cluster boundaries and zero sensor noise. In actual agricultural fields, micro-climates, soil depth variations, and pest pressures introduce significant noise not captured in tabular benchmark datasets.

---

## 3. Fertilizer Recommendation Model — Decision Tree (Prototype)

### 3.1 Model Specifications
* **Architecture:** Scikit-Learn `DecisionTreeClassifier` with categorical label encoding for soil and crop types, followed by standard scaling.
* **Input Features (8):** `Temparature`, `Humidity`, `Moisture`, `Soil Type`, `Crop Type`, `Nitrogen`, `Potassium`, `Phosphorous`.
* **Output Classes (7):** `10-26-26`, `14-35-14`, `17-17-17`, `20-20`, `28-28`, `DAP`, `Urea`.

### 3.2 Domain Safeguards & Alluvial Soil Handling
* **The Problem:** The underlying Kaggle fertilizer dataset contains only 5 soil labels (`Black`, `Clayey`, `Loamy`, `Red`, `Sandy`), whereas real-world soils (and the CNN classifier) identify `Alluvial` soils. Alluvial soil is a broad fluvial pedological group that can range physically from coarse sand to dense clay.
* **The Safeguard:** In `analysis_service.py` and `fertilizer_model.py`, if a soil is identified as Alluvial and no mechanical texture is confirmed, the fertilizer prediction is withheld (`status="unsupported"`). Once a valid physical texture (`confirmed_soil_texture`) is confirmed, the model executes safely.

---

## 4. Soil Visual Classification — MobileNetV2 CNN

### 4.1 Dataset Forensic Audit & Perceptual Deduplication
Prior to Phase 6, the raw soil dataset contained 671 images. A forensic audit utilizing cryptographic (SHA-256) and perceptual difference hashing (`dHash`) revealed significant data leakage:
* 70 exact duplicate matches across train/validation/test splits.
* 299 near-duplicate image pairs with Hamming distance $\le 4$.
* Two `.webp` files silently skipped due to casing extensions.

**Deduplication Implementation (Phase 6, Task P1.1):**
* Removed all intra-split and cross-split duplicate groups.
* Standardized all images to canonical RGB JPEG format.
* Created clean dataset: **470 verified canonical images** in `backend/ml_training/datasets/soil_images_clean/`.
* Created official leakage-free split metadata: `backend/trained_models/soil_cnn_splits_v2.json`.
  * **Training Split:** 329 images (70%)
  * **Validation Split:** 70 images (15%)
  * **Test Split:** 71 images (15%) — strictly isolated and held out.

### 4.2 Architecture & Preprocessing
* **Base Network:** MobileNetV2 pretrained on ImageNet ($3.4\times 10^6$ parameters).
* **Head Network:** `GlobalAveragePooling2D` $\rightarrow$ `Dense(128, ReLU)` $\rightarrow$ `Dropout(0.3)` $\rightarrow$ `Dense(4, Softmax)`.
* **Input Dimensions:** $224 \times 224 \times 3$ RGB.
* **Normalization:** Scaled to $[-1, 1]$ via `tf.keras.applications.mobilenet_v2.preprocess_input`.

### 4.3 Model V1 (Production) vs Model V2 (Experimental) Evaluation

Both models were evaluated on the exact same **71 clean, leakage-free test images**:

```
                              SOIL CNN PERFORMANCE COMPARISON
  ┌───────────────────────┬──────────────────────────┬──────────────────────────┐
  │ Metric                │ Model V1 (Production)    │ Model V2 (Experimental)  │
  ├───────────────────────┼──────────────────────────┼──────────────────────────┤
  │ Overall Test Accuracy │ 81.69% (58 / 71 correct) │ 80.28% (57 / 71 correct) │
  │ Macro F1-Score        │ 81.62%                   │ 80.48%                   │
  │ Alluvial Recall       │ 78.95% (15 / 19)         │ 84.21% (16 / 19)         │
  │ Black Soil Recall     │ 88.89% (16 / 18)         │ 66.67% (12 / 18)         │
  │ Clay Soil Recall      │ 66.67% (10 / 15)         │ 73.33% (11 / 15)         │
  │ Red Soil Recall       │ 89.47% (17 / 19)         │ 94.74% (18 / 19)         │
  └───────────────────────┴──────────────────────────┴──────────────────────────┘
```

#### Diagnostic Decision:
* **Model V1 is frozen as the active production model.** It maintains superior balance across all four classes, particularly for Black soil (88.89% vs 66.67%).
* **Model V2 is archived as an experimental comparative study.** While V2 improved Clay and Red detection through aggressive learning-rate decay, it caused feature suppression for dark organic Black soils. Retaining V2 as an ablation artifact provides valuable defense material for academic viva examinations.

---

## 5. Smart Irrigation Engine — Dynamic Rule Engine

### 5.1 Agronomic Foundation
Irrigation advice is calculated deterministically using principles derived from the **FAO-56 Penman-Monteith** evapotranspiration model, adjusted for sensor soil moisture deficits, ambient temperature, and soil drainage characteristics:

$$\text{Effective Moisture} = \text{Raw Moisture} + \Delta_{\text{soil}} - \Delta_{\text{crop}}$$

### 5.2 Soil Drainage Modifiers ($\Delta_{\text{soil}}$)
The engine incorporates documented agronomic drainage tendencies while enforcing safe fallbacks:

```python
_SOIL_MODIFIER = {
    # Hydraulic Textures (USDA particle-size classes)
    "Sandy":    -8.0,   # Fast percolation; effective moisture lower than measured
    "Loamy":     0.0,   # Neutral agronomic baseline
    "Silty":    +3.0,   # Moderate retention
    "Clay":     +8.0,   # High specific surface area; strong moisture retention
    "Clayey":   +8.0,   # Alias for Clay
    # Pedological Classes (MobileNetV2 Visual CNN outputs)
    "Black":    +6.0,   # Vertisol/Regur swelling clay mineral heuristic
    "Red":      -4.0,   # Alfisol well-drained / coarse loam heuristic
    "Alluvial":  0.0,   # Fluvial deposit baseline; textural test required for offset
}
```

* **Textural Priority:** If laboratory analysis or user-confirmed texture (`soil_texture`) is present, it strictly overrides the visual CNN classification.
* **Safe Neutral Fallback:** Any unrecognized or missing soil type defaults to `0.0%` (Loamy baseline), preventing sensor distortion.

---

## 6. Model Verification & Cryptographic Checksums

To verify model immutability and provenance, SHA-256 cryptographic hashes are recorded:

```text
crop_rf_v1.pkl              4ADC3B7DF6314B40D7B1262EDB888FBE46D677B58C5583B3A54324802253D6B1
crop_scaler.pkl             3A1DCBDDAF02D8DE77CD81AA29B1A4630F8E6FB6FF7878E13BB5FB026E12CB3A
fertilizer_dt_prototype.pkl 4CBD9ABA9626BC7BFA919811B57E9223575A4C13B7A33E26A62F95FEDBF0A5DC
fertilizer_encoders.pkl     58613D54A9E85715C35262125AFD5E7FC1D9451E04E815ACBE5FD62C9BBE8AF4
fertilizer_scaler.pkl       4E9D740A26257DC6B4BB04E6026E329C3239204C7552F977A8D98AC5B918CD94
soil_cnn_v1.h5              EB99065E1B40A1EDCF7A498C659659E854D8C980BF368C748AAD618B93A3D726
soil_cnn_classes.pkl        DD112CBA5899DE77C416F83E60ED06BA2475D8C3E4E3F668E9A13069A2AAE724
soil_cnn_splits_v2.json     3B5AB8E76E159EFA4433908AE586F5AD1E041EE1C4C91CF681749AA10EE6A29E
soil_cnn_v2.h5              4CA7087EFAAE781B965C2C9749149CEAD369698FCFDAD88E1AE02E2F052D7B92
```

---
*End of ML Pipeline Guide.*
