# AgroSmart — Dataset Inventory, Provenance & Licensing Guide

This directory documents the dataset sources, forensic deduplication artifacts, split metadata, and licensing boundaries utilized across AgroSmart's machine learning pipelines.

---

## 1. Crop Recommendation Dataset
* **Source:** [Kaggle — Crop Recommendation Dataset](https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset)
* **File Name:** `crop_recommendation.csv`
* **Sample Count:** 2,200 rows (100 per crop class across 22 classes)
* **Features:** Nitrogen ($N$), Phosphorus ($P$), Potassium ($K$), Temperature, Humidity, pH, Rainfall
* **Trained Model:** `trained_models/crop_rf_v1.pkl` (Random Forest, 99.09% accuracy on 440 test samples)
* **Status:** Pre-trained and bundled in repository.

---

## 2. Fertilizer Recommendation Dataset (Prototype)
* **Source:** [Kaggle — Fertilizer Prediction](https://www.kaggle.com/datasets/gdabhishek/fertilizer-prediction)
* **File Name:** `fertilizer_recommendation.csv`
* **Features:** Temperature, Humidity, Moisture, Soil Type, Crop Type, Nitrogen, Potassium, Phosphorus
* **Target Classes:** 7 formulations (10-26-26, 14-35-14, 17-17-17, 20-20, 28-28, DAP, Urea)
* **Trained Model:** `trained_models/fertilizer_dt_prototype.pkl` (Decision Tree)
* **Domain Safeguard:** Alluvial soil texture safeguard enforced in `fertilizer_model.py`.

---

## 3. Soil Visual Classification Dataset (CNN)

### Forensic Deduplication & Clean Dataset (Phase 6, Task P1.1)
* **Original Dataset:** `soil_images/` (671 raw images across 4 classes: Alluvial, Black, Clay, Red).
* **Audit Findings:** Perceptual dHash analysis identified 70 exact cross-split duplicate pairs and 299 near-duplicates ($\text{Hamming distance} \le 4$).
* **Clean Canonical Dataset:** `soil_images_clean/`
  * Contains **470 deduplicated RGB JPEG images** (201 duplicate/corrupt scenes removed).
  * Class Breakdown:
    * `Alluvial/`: 126 canonical images
    * `Black/`: 119 canonical images
    * `Clay/`: 100 canonical images
    * `Red/`: 125 canonical images
* **Audit Manifest:** `soil_images_manifest.json` (Per-image cryptographic SHA-256 and perceptual dHash metadata).
* **Official Leakage-Free Splits:** `backend/trained_models/soil_cnn_splits_v2.json`
  * **Train Set:** 329 images (70%)
  * **Validation Set:** 70 images (15%)
  * **Test Set:** 71 images (15% — strictly held out for final evaluation)
* **Trained Models:**
  * `trained_models/soil_cnn_v1.h5` (**Production Model:** 81.69% accuracy on 71 clean test images).
  * `trained_models/soil_cnn_v2.h5` (*Experimental Ablation Model:* 80.28% accuracy).

---

## 4. Public Distribution & Licensing Notice for Image Datasets

> [!IMPORTANT]
> **Notice on Image Binary Exclusion:**
> The physical image directories (`backend/ml_training/datasets/soil_images/` and `backend/ml_training/datasets/soil_images_clean/`) are **intentionally excluded from public Git distribution** via `.gitignore`.

### Rationale & Legal Compliance
A forensic legal and copyright audit ([`docs/finalization/soil_dataset_license_audit.md`](../../docs/finalization/soil_dataset_license_audit.md)) revealed that the underlying image collection incorporates commercial stock photography (including verified assets from Adobe Stock and Dreamstime) and web-scraped images for which public redistribution and open-source sublicensing rights could not be established.

### Scientific Auditability & Reproducibility Architecture
To maintain complete scientific auditability without infringing third-party copyrights:
1. **Public Cryptographic Manifest:** The full dataset metadata is publicly tracked in [`soil_images_manifest.json`](soil_images_manifest.json). This manifest documents exact SHA-256 hashes, MD5 checksums, 64-bit perceptual dHash/pHash fingerprints, dimensions, color channels, and duplicate cluster mappings for all 671 original and 470 canonical images.
2. **Deterministic Partition Metadata:** The official train/validation/test split mapping is publicly tracked in `backend/trained_models/soil_cnn_splits_v2.json`.
3. **Researcher Notice:** External researchers and developers wishing to retrain or benchmark the Soil CNN must independently obtain appropriately licensed soil surface imagery (or collect their own field photography) conforming to the class schema (`Alluvial`, `Black`, `Clay`, `Red`).
4. **Academic Examination & Viva Defense:** For local university evaluation and viva voce defense, the clean dataset is preserved locally and bundled with the offline submission archive under educational fair use provisions.

---
*End of Dataset Inventory.*
