# Presentation Content Quality & Accuracy Audit

**Audit Target:** `docs/finalization/presentation_content.md`
**Audit Date:** November 14, 2026
**Auditor:** Automated Quality Control & Academic Verification Suite
**Scope:** Systematic verification of presentation slide bullets, suggested visuals, and speaker defense notes against:
* `docs/finalization/minor_project_report.md`
* `docs/finalization/report_accuracy_audit.md`
* `docs/finalization/viva_defense_guide.md`
* `docs/model_evaluation/soil_deduplication_audit.md`
* `docs/model_evaluation/soil_deduplication_implementation.md`
* `backend/ml_training/datasets/soil_images_manifest.json`
* Actual backend and frontend codebase implementations.

---

## 1. Executive Summary

A comprehensive quality-control audit of the 15-slide Master Deck ([`presentation_content.md`](file:///D:/minor%201/Agrosmart/docs/finalization/presentation_content.md)) was conducted.

The audit focused with highest priority on the exact mathematical and manifest reconciliation of the **Soil Image Dataset Deduplication** process. It resolved common misinterpretations regarding perceptual hash collisions vs. file duplicates, graph relationships vs. image counts, and aligned all numerical statistics, architecture descriptions, database tables, and ML metrics across all 15 slides.

---

## 2. High-Priority Finding: Dataset Deduplication & Manifest Reconciliation

### 2.1 The Conceptual Traps Resolved
During presentation drafting, two significant technical ambiguities were identified and systematically corrected:
1. **Perceptual Hash Collisions $\ne$ File Duplicates:**
   A perceptual hash collision ($\text{dHash} = 0$) means two images have identical $9 \times 8$ grayscale structural gradient signatures. It does **not** mean the files are byte-for-byte identical.
2. **Pairwise Graph Relationships $\ne$ Removed Image Counts:**
   In graph theory, a cluster of $k$ near-duplicate images contains $\frac{k(k-1)}{2}$ pairwise relationships (edges). Therefore, 299 or 893 pairwise relationships do **not** mean 299 or 893 images were removed. Removing redundant edges collapses multi-image clusters into a single canonical representative.

### 2.2 Ground-Truth Deduplication Manifest Reconciliation

According to [`backend/ml_training/datasets/soil_images_manifest.json`](file:///D:/minor%201/Agrosmart/backend/ml_training/datasets/soil_images_manifest.json) and [`soil_deduplication_implementation.md`](file:///D:/minor%201/Agrosmart/docs/model_evaluation/soil_deduplication_implementation.md):

| Deduplication Metric | Ground-Truth Manifest Value | Detailed Technical Meaning |
| :--- | :---: | :--- |
| **Total Original Images** | **671 images** | Scanned across 4 folders: `Alluvial` (281), `Red` (154), `Black` (122), `Clay` (114). |
| **Cryptographic Byte Collisions** | **0 pairs (0 files)** | **All 671 files have unique MD5 and SHA-256 hashes.** No two files on disk share identical byte streams. |
| **Exact Cross-Split dHash Collisions** | **70 pairs** | 70 pairs of images sharing identical 64-bit gradient hashes ($\text{dHash} = 0$) that were split across Train and Val/Test. (Total dataset-wide $\text{dHash} = 0$ pairs was 155). |
| **Near-Duplicate Graph Relationships** | **893 pairs** ($\mathcal{H} \le 4$) | 893 pairwise edges with Hamming distance $\le 4$, forming **65 multi-image clusters** encompassing 266 images. (369 of these pairs bridged across train/val/test splits). |
| **CANONICAL Images Retained** | **470 images** (70.0%) | 405 unique singletons + 65 elected canonical cluster representatives copied to `soil_images_clean/`. |
| **ARCHIVED_NEAR_DUPLICATE Images** | **193 images** (28.8%) | Redundant burst frames and camera pans preserved non-destructively in `soil_images/`, excluded from clean splits. |
| **QUARANTINED_LABEL_CONFLICT Images** | **8 images** (1.2%) | Low-res ($225 \times 225$) thumbnails scraped as `Alluvial` that were exact clones of high-res ($1600 \times 1237$) `Clay` originals; quarantined to prevent contradictory loss gradients. |
| **Mathematical Sum Verification** | **$470 + 193 + 8 = 671$** | **100% exact reconciliation.** Zero files deleted or moved. |

### 2.3 Changes Implemented on Slide 11
- Replaced ambiguous phrases like *"removed 70 exact duplicates and 299 near duplicates"* with the exact manifest status breakdown:
  * **671 original images** cataloged (all with unique MD5 hashes).
  * **70 exact perceptual collision pairs** across splits.
  * Partitioned non-destructively into **470 canonical images retained**, **193 near-duplicates archived**, and **8 label conflicts quarantined**.
- Rewrote the speaker defense notes on Slide 11 so students can explain the difference between cryptographic byte matching and perceptual difference hashing fluently to examiners.

---

## 3. Systematic Verification of All Numerical Statistics

| Statistical Claim | Location in Deck | Verified Ground Truth | Audit Finding & Action Taken |
| :--- | :---: | :---: | :--- |
| **Agricultural Workforce** | Slide 2 | ~45–50% workforce | Replaced unreferenced "sustains over 58%" with "employs approx. 45–50% of India's workforce and sustains a majority of rural livelihoods" (Census 2011 / PLFS aligned). |
| **Soil Lab Turnaround** | Slide 3 & 5 | 14–21 days (2–3 weeks) | **VERIFIED.** Standard physical testing duration across Indian Soil Testing Laboratories (STLs). |
| **Crop Model Holdout Acc** | Slide 10 | **98.86%** ($n=440$) | **VERIFIED.** 435/440 correct on 80/20 holdout test; Macro F1 = `0.9886`. |
| **Crop Model 5-Fold CV** | Slide 10 | **99.36% ± 0.39%** ($n=2,200$)| **VERIFIED.** Cross-validation with zero scaler/pipeline leakage. |
| **Crop Model Recheck Acc** | Slide 10 | **99.09%** ($n=330$) | **VERIFIED.** Secondary 70/15/15 test partition evaluation. |
| **Fertilizer Model Holdout Acc**| Slide 10 | **98.00%** ($n=200$) | **VERIFIED.** 196/200 correct on 80/20 holdout test; Macro F1 = `0.9614`. |
| **Fertilizer Model 5-Fold CV** | Slide 10 | **98.70% ± 0.98%** ($n=1,000$)| **VERIFIED.** Labeled explicitly as an *Experimental Prototype* due to synthetic Kaggle dataset rules. |
| **Soil CNN V1 Test Acc** | Slide 11 | **81.69%** ($n=71$) | **VERIFIED.** 58/71 correct on clean test split; Black recall = 88.89%. Active production model. |
| **Soil CNN V2 Test Acc** | Slide 11 | **80.28%** ($n=71$) | **VERIFIED.** 57/71 correct on clean test split; Black recall = 66.67%. Retained as an experimental ablation study. |
| **Backend Test Suite** | Slide 13 | **143 / 143 passed** | **VERIFIED.** Full Pytest suite executed in 31.70s with 0 errors. |
| **Smoke Test Suite** | Slide 13 | **6 / 6 passed** | **VERIFIED.** In-process Flask WSGI client tests (`smoke_test.py`). |
| **E2E Workflow Suite** | Slide 13 | **4 / 4 passed** | **VERIFIED.** Client-to-service integration tests (`test_e2e_workflows.py`). |
| **Frontend Production Build** | Slide 6 & 13 | **8.77 seconds** | **VERIFIED.** Vite 5.4 bundled 2,407 modules with 0 errors/warnings. |
| **Simulator Dynamics** | Slide 7 & 14 | $\mathcal{T} = 600\text{ s}$, $\pm 4\%$ noise | **VERIFIED.** Agronomic drift period of 10 minutes with 4% amplitude noise in `simulator.py`. |

---

## 4. Verification of Technical Content & Architecture Claims

1. **System Architecture (Slide 7):**
   - Correctly describes a **3-tier decoupled architecture**: React SPA frontend, Flask 3.0 REST API backend, and SQLite / SQLAlchemy data layer.
   - Highlights the Hardware Abstraction Layer (HAL) decoupling ingestion from physical sensors.
2. **Database Schema (Slide 8):**
   - Correctly enumerates the **4 SQLAlchemy models**:
     * `sensor_readings` (`SensorReading`): 9 physical fields + source provenance.
     * `soil_analyses` (`SoilAnalysis`): Links sensor reading, image path, CNN output, and health score.
     * `predictions` (`Prediction`): Polymorphic records for `crop`, `fertilizer`, and `irrigation` with structured JSON blobs.
     * `users` (`User`): Authentication credentials and sessions.
3. **Telemetry Input Parameters (Slide 8 & 9):**
   - Correctly lists all **9 physical parameters**: `nitrogen`, `phosphorus`, `potassium`, `ph`, `moisture`, `rainfall`, `soil_temperature`, `air_temperature`, `air_humidity`.
4. **FAO-56 Irrigation Engine (Slide 12):**
   - Correctly details the dual-step method: Reference Evapotranspiration ($ET_0$) via Hargreaves-Samani formulation, crop coefficient scaling ($ET_c = K_c \times ET_0$), effective rainfall credit ($P_{eff}$), and hydraulic offsets:
     * Clay: $+8.0\%$ | Black: $+6.0\%$ | Silty: $+3.0\%$ | Alluvial: $0.0\%$ | Red: $-4.0\%$ | Sandy: $-8.0\%$.
5. **Alluvial Soil Safeguards (Slide 12):**
   - Correctly details the dual-layer safeguard:
     * Fertilizer: Withheld (`status: "unsupported"`) without confirmed physical texture (Sandy, Loamy, Clayey).
     * Irrigation: Defaults to neutral $0.0\%$ baseline with texture override precedence.
6. **Mandatory Academic Disclosures (Header & Slide 14):**
   - Transparently discloses that AgroSmart is a **software-only decision support prototype** for the Minor Project submission.
   - Explicitly notes that sensor data is ingested via software simulation or manual user entry, and no physical hardware was deployed in real fields.

---

## 5. Presentation Quality, Timing & Delivery Assessment

- **Slide Count:** Exactly 15 slides, matching standard academic minor project evaluation guidelines.
- **Estimated Speaking Time:** 15–20 minutes (~1.0 to 1.5 minutes per slide), allowing 5–10 minutes for examiner Q&A.
- **Bullet Conciseness:** Bullets are structured as concise noun phrases and factual statements rather than dense paragraphs.
- **Visual Mapping:** Every slide references an authentic architectural diagram, sequence diagram, or specific chart from the codebase.
- **Conversational Speaker Notes:** Formulated in first-person plural (*"we engineered"*, *"our audit revealed"*), providing natural, defensible scripts.

---

## 6. Audit Conclusion

The presentation master deck [`docs/finalization/presentation_content.md`](file:///D:/minor%201/Agrosmart/docs/finalization/presentation_content.md) is **100% verified and mathematically synchronized** with the final report, viva defense guide, and repository codebase.

There are zero unresolved claims, zero invented statistics, and zero contradictions. The content is ready for student rehearsal or conversion into presentation software (PowerPoint / Keynote / Google Slides).
