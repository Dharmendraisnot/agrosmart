# AgroSmart Phase 6 (Task P1) — Comprehensive Machine Learning Model Evaluation Report

**Project:** AgroSmart — AI-Based Soil Analysis & Crop Recommendation System
**Phase / Task:** Phase 6 — Task P1: Comprehensive Machine Learning Model Evaluation (Read-Only Baseline Audit)
**Scope:** Crop Recommendation (`RandomForestClassifier`), Fertilizer Recommendation (`DecisionTreeClassifier` prototype), and Soil Image Classification (`MobileNetV2` CNN), plus data preprocessing, training/evaluation scripts, saved artifacts, and production inference pipelines.

---

## 1. Executive Summary

This audit established a reproducible, leakage-free performance baseline across all three machine learning models currently deployed in AgroSmart without modifying any model artifacts, training datasets, or production code.

| Model | Algorithm & Artifact | Dataset & Split | Train Acc | Val / CV-5 Acc | Held-Out Test Acc | Macro F1 | Production Readiness |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Crop Recommendation** | `RandomForestClassifier` (`crop_rf_v1.pkl`) | **Synthetic** tabular (`2,200` rows, `22` balanced classes, 80/20 split: `1,760` / `440`) | `100.00%` | `99.36% ± 0.39%` *(leakage-free 5-fold CV)* | **`98.86%`** *(435/440)* | **`0.9886`** | **Synthetic Benchmark Only** — accurately separates uniform synthetic intervals, but lacks real agronomic covariance and suffers simulator/default `K` and `rainfall` mismatches. |
| **Fertilizer Recommendation** | `DecisionTreeClassifier` (`fertilizer_dt_prototype.pkl`) | **Synthetic** tabular (`1,000` rows, `7` imbalanced classes, 80/20 split: `800` / `200`) | `99.88%` | `98.70% ± 0.98%` *(leakage-free 5-fold CV)* | **`98.00%`** *(196/200)* | **`0.9614`** | **Unsafe Prototype** — recovers 7 synthetic `if/elif` rules; assigns **`0.0000`** importance to `Crop Type`, `Temperature`, and `Humidity`. |
| **Soil Image Classification** | `MobileNetV2` Transfer Learning (`soil_cnn_v1.h5`) | **Real Images** (`671` total, `4` imbalanced classes, 70/15/15 split: `469*` / `101` / `101`) | `89.72%` *(unaug, n=467)* | `86.14%` *(Stage 1 Ep 5, n=101)* | **`90.10%`** *(91/101)* | **`0.8882`** | **Conditional Prototype** — best grounded model, but test accuracy is likely **optimistically inflated** by `70` exact perceptual dHash collisions across splits and weak `Black` soil recall (`66.67%`). |

> **Important Comparability Warning:** Raw accuracy percentages **must not be compared directly** across the tabular models (`98.86%`, `98.00%`) and the image classifier (`90.10%`). Both tabular models were trained and tested on 100% deterministically generated synthetic CSV datasets (`generate_synthetic_datasets.py`, seed `42`), whereas the Soil CNN was evaluated on real soil photographs exhibiting class imbalance, lighting variation, and visual overlap.

---

## 2. Files & Components Inspected

* **Training & Data Scripts (`backend/ml_training/`):**
  * [generate_synthetic_datasets.py](file:///D:/minor%201/Agrosmart/backend/ml_training/generate_synthetic_datasets.py)
  * [preprocessing_pipeline.py](file:///D:/minor%201/Agrosmart/backend/ml_training/preprocessing_pipeline.py)
  * [train_crop_model.py](file:///D:/minor%201/Agrosmart/backend/ml_training/train_crop_model.py)
  * [train_fertilizer_model.py](file:///D:/minor%201/Agrosmart/backend/ml_training/train_fertilizer_model.py)
  * [train_soil_cnn.py](file:///D:/minor%201/Agrosmart/backend/ml_training/train_soil_cnn.py)
  * [evaluate_models.py](file:///D:/minor%201/Agrosmart/backend/ml_training/evaluate_models.py)
  * [datasets/README.md](file:///D:/minor%201/Agrosmart/backend/ml_training/datasets/README.md)
* **Saved Artifacts (`backend/trained_models/`):** `crop_rf_v1.pkl`, `crop_scaler.pkl`, `fertilizer_dt_prototype.pkl`, `fertilizer_encoders.pkl`, `fertilizer_scaler.pkl`, `soil_cnn_v1.h5`, `soil_cnn_classes.pkl`, `soil_cnn_metrics.json`, `soil_cnn_splits.json`
* **Production Inference & Services (`backend/app/`):**
  * [crop_model.py](file:///D:/minor%201/Agrosmart/backend/app/ml/crop_model.py)
  * [fertilizer_model.py](file:///D:/minor%201/Agrosmart/backend/app/ml/fertilizer_model.py)
  * [soil_cnn.py](file:///D:/minor%201/Agrosmart/backend/app/ml/soil_cnn.py)
  * [preprocessor.py](file:///D:/minor%201/Agrosmart/backend/app/ml/preprocessor.py)
  * [image_service.py](file:///D:/minor%201/Agrosmart/backend/app/services/image_service.py)
  * [analysis_service.py](file:///D:/minor%201/Agrosmart/backend/app/services/analysis_service.py)
  * [recommendation_service.py](file:///D:/minor%201/Agrosmart/backend/app/services/recommendation_service.py)
  * [simulator.py](file:///D:/minor%201/Agrosmart/backend/app/hardware/simulator.py)
* **Environment & Documentation:** [requirements.txt](file:///D:/minor%201/Agrosmart/backend/requirements.txt), [docs/ml-pipeline.md](file:///D:/minor%201/Agrosmart/docs/ml-pipeline.md)

---

## 3. Dataset Provenance & Integrity Audit

### 3.1 Tabular Datasets (`crop_recommendation.csv` & `fertilizer_recommendation.csv`)

Exact comparison of both CSV files on disk against fresh runs of `generate_synthetic_datasets.py` (`seed = 42`) confirmed **`crop_matches_synthetic_generator_exactly: true`** and **`fertilizer_matches_synthetic_generator_exactly: true`**.

1. **Crop Dataset (`crop_recommendation.csv`):**
   * **Rows / Columns:** `2,200` rows, `8` columns (`N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`, `label`). `0` nulls, `0` duplicates.
   * **Class Distribution:** `22` classes × `100` rows each (perfectly balanced).
   * **Observed Numeric Ranges:**
     * `N`: `0.09 – 139.83` | `P`: `0.19 – 90.00` | `K`: `5.02 – 89.69` *(mean `36.71`)*
     * `temperature`: `8.49 – 37.99` | `humidity`: `15.19 – 95.00` | `ph`: `3.51 – 8.00` | `rainfall`: `20.03 – 298.55`
   * **Limitation:** Values are drawn independently from class-wise uniform box intervals rounded to 2 decimals. Real-world soil nutrient covariance, seasonal weather coupling, and regional outliers are absent.

2. **Fertilizer Dataset (`fertilizer_recommendation.csv`):**
   * **Rows / Columns:** `1,000` rows, `9` columns (`Temperature`, `Humidity`, `Moisture`, `Soil Type`, `Crop Type`, `Nitrogen`, `Potassium`, `Phosphorous`, `Fertilizer Name`). `0` nulls, `0` duplicates.
   * **Severe Class Imbalance (7 classes):** `17-17-17` (`247`), `Urea` (`180`), `14-35-14` (`172`), `28-28` (`136`), `DAP` (`131`), `20-20` (`81`), `10-26-26` (`53`).
   * **Categorical Distribution:**
     * `Soil Type` (5): `Red` (`215`), `Black` (`204`), `Clayey` (`198`), `Loamy` (`192`), `Sandy` (`191`).
     * `Crop Type` (12): `Pulses` (`104`), `Kidneybeans` (`94`), `Cotton` (`89`), `Barley` (`87`), `Millets` (`84`), `Ground Nuts` (`83`), `Oil seeds` (`83`), `Tobacco` (`82`), `Wheat` (`77`), `Sugarcane` (`76`), `Paddy` (`76`), `Maize` (`65`).
   * **Root Structural Flaw:** `generate_synthetic_datasets.py` assigns `Fertilizer Name` via 7 deterministic `if/elif` rules over **only** `Nitrogen`, `Phosphorous`, `Potassium`, `Moisture`, and `Soil Type`. `Crop Type`, `Temperature`, and `Humidity` are sampled uniformly at random and **never consulted** in label generation.

### 3.2 Soil Image Dataset (`backend/ml_training/datasets/soil_images/`)

* **Total Images & Class Imbalance:** `671` images across `4` classes (`2.46×` majority-to-minority ratio):
  * `Alluvial`: `281` (`41.9%`) | `Red`: `154` (`23.0%`) | `Black`: `122` (`18.2%`) | `Clay`: `114` (`17.0%`)
* **Image Format & Geometry:** Modes `RGB` (`667`), `P` (`2`), `RGBA` (`2`). Widths `100–2,592 px` (median `390 px`), heights `57–1,920 px` (median `280 px`).
* **Split Integrity Defects Discovered:**
  1. **Silent `.webp` Exclusion (`469` recorded -> `467` trained):** `load_dataset_catalog()` in `train_soil_cnn.py` allows `.webp`, placing `alluvial_0032.webp` and `black_0092.webp` into the `469`-image train split in `soil_cnn_splits.json`, but `ImageDataGenerator.flow_from_dataframe` silently skipped both files.
  2. **Perceptual Near-Duplicate Leakage Across Splits:** While exact byte-level MD5 deduplication found **`0` cross-split overlaps**, a 64-bit perceptual difference hash (`dHash`) audit detected **`70` cross-split exact dHash collisions (`hamming_dist == 0`)** and **`299` cross-split near-duplicate pairs (`hamming_dist <= 4`)**, alongside `85` within-split exact dHash collisions. Re-saved, resized, or re-compressed copies of identical soil photographs exist in both training and validation/test partitions, artificially inflating validation and test accuracy.

---

## 4. Detailed Model Evaluations

### 4.1 Model A — Crop Recommendation (`RandomForestClassifier`)

![Crop Recommendation Random Forest Evaluation](file:///D:/minor%201/Agrosmart/docs/model_evaluation/crop_rf_evaluation.png)

* **Configuration & Structure:** `n_estimators=100`, `max_depth=None`, `min_samples_split=2`, `random_state=42`. Inspected tree depths span `11–19` (mean `14.33`), mean leaf count `66.89`.
* **Split Verification:** Exact stratified 80/20 split (`1,760` train / `440` test, `20` samples per crop); saved `crop_scaler.pkl` matches the `1,760`-row training split (`scaler_matches_train_split: true`).
* **Verified Performance Metrics:**
  * **Train Accuracy:** `1.0000` (`100.00%`)
  * **Held-Out Test Accuracy (n=440):** `0.9886` (`98.86%`, `435/440` correct) — Overfit gap: `0.0114` (`1.14%`)
  * **Macro Precision / Recall / F1:** `0.9899` / `0.9886` / `0.9886`
  * **Weighted Precision / Recall / F1:** `0.9899` / `0.9886` / `0.9886`
  * **Leakage-Free 5-Fold Stratified CV (`Pipeline`):** **`0.9936 ± 0.0039`** (folds: `0.9932, 0.9955, 0.9864, 0.9977, 0.9955`)
  * **70/15/15 Stratified Recheck:** Validation `0.9939`, Test `0.9909`
* **Error Analysis (5/440 Test Misclassifications):**
  * `pigeonpeas -> mungbean` (`3` errors): `pigeonpeas` Recall `0.8500`, Precision `1.0000`, F1 `0.9189`; `mungbean` Precision `0.8696`, Recall `1.0000`, F1 `0.9302`.
  * `apple -> pomegranate` (`2` errors): `apple` Recall `0.9000`, Precision `1.0000`, F1 `0.9474`; `pomegranate` Precision `0.9091`, Recall `1.0000`, F1 `0.9524`.
  * **Remaining 18 Crops:** Precision `1.0000`, Recall `1.0000`, F1 `1.0000` (`support = 20` each).
* **Gini Feature Importances:** `rainfall` (`0.2474`) > `humidity` (`0.2322`) > `N` (`0.1565`) > `K` (`0.1318`) > `P` (`0.1257`) > `temperature` (`0.0714`) > `ph` (`0.0350`).
* **Pipeline & Inference Findings:**
  * **Training Script Leakage:** `train_crop_model.py:106` runs `cross_val_score(model, scaler.transform(X), y, cv=5)` after scaling on training data and evaluating on full `X`, and `print_metrics()` (`line 168`) re-fits `StandardScaler().fit(X)` on full `X`.
  * **Production Domain Shift:** `simulator.py` uses `potassium` range `40.0–350.0` (`baseline = 180.0`) and `CropInferencePreprocessor._CROP_MEDIANS["potassium"] = 180.0`, both far above the training distribution max (`K = 89.69`). Moreover, simulated sensor packets set `rainfall = None`, forcing `CropInferencePreprocessor` to inject a constant fallback `_CROP_MEDIANS["rainfall"] = 52.0` on the model's **#1 most important feature** (`0.2474`).

---

### 4.2 Model B — Fertilizer Recommendation (`DecisionTreeClassifier` Prototype)

![Fertilizer Recommendation Decision Tree Audit](file:///D:/minor%201/Agrosmart/docs/model_evaluation/fertilizer_dt_evaluation.png)

* **Configuration & Structure:** `DecisionTreeClassifier(max_depth=10, min_samples_split=5, criterion="gini", random_state=42)`. Resulting tree depth is `7` with `16` leaves.
* **Split Verification:** Exact stratified 80/20 split (`800` train / `200` test); `fertilizer_scaler.pkl` matches the `800`-row training split (`scaler_matches_train_split: true`), though `LabelEncoder` was fit on the full dataset prior to splitting (`train_fertilizer_model.py`).
* **Verified Performance Metrics:**
  * **Train Accuracy:** `0.9988` (`99.88%`)
  * **Held-Out Test Accuracy (n=200):** `0.9800` (`98.00%`, `196/200` correct) — Overfit gap: `0.0188`
  * **Macro Precision / Recall / F1:** `0.9735` / `0.9521` / `0.9614`
  * **Weighted Precision / Recall / F1:** `0.9795` / `0.9800` / `0.9791`
  * **Leakage-Free 5-Fold Stratified CV (`Pipeline`):** **`0.9870 ± 0.0098`** (folds: `1.0000, 0.9850, 0.9900, 0.9900, 0.9700`)
  * **70/15/15 Stratified Recheck:** Validation `0.9933`, Test `0.9867`
* **Per-Class Test Classification Report (`n = 200`):**

| Fertilizer Class | Precision | Recall | F1-Score | Test Support | Train+Test Total | Error Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`10-26-26`** | `0.8889` | **`0.7273`** | **`0.8000`** | `11` | `53` | `8/11` correct (`2` -> `17-17-17`, `1` -> `28-28`) |
| `20-20` | `1.0000` | `0.9375` | `0.9677` | `16` | `81` | `15/16` correct (`1` -> `10-26-26`) |
| `17-17-17` | `0.9615` | `1.0000` | `0.9804` | `50` | `247` | `50/50` correct (`2` false positives from `10-26-26`) |
| `28-28` | `0.9643` | `1.0000` | `0.9818` | `27` | `136` | `27/27` correct (`1` false positive from `10-26-26`) |
| `14-35-14` | `1.0000` | `1.0000` | `1.0000` | `34` | `172` | `34/34` correct |
| `DAP` | `1.0000` | `1.0000` | `1.0000` | `26` | `131` | `26/26` correct |
| `Urea` | `1.0000` | `1.0000` | `1.0000` | `36` | `180` | `36/36` correct |

* **Feature Importances & Zero-Weight Proof:**
  * `nitrogen`: `0.2636` | `phosphorus`: `0.2269` | `soil_type`: `0.1855` | `potassium`: `0.1747` | `moisture`: `0.1493`
  * **`temperature`: `0.0000` | `humidity`: `0.0000` | `crop_type`: `0.0000`**
* **Real-World Suitability Audit:** **Unsuitable for real agricultural fertilizer dosing.** The `98.00%` accuracy merely confirms that a depth-7 decision tree can reverse-engineer 7 synthetic `if/elif` rules. Changing the recommended crop (e.g., Wheat vs Paddy vs Sugarcane) has **zero influence** on tree splits. In addition, `Soil Type` and `Crop Type` are integer-encoded (`LabelEncoder`) and passed into `StandardScaler`—imposing false ordinal spacing—while synthetic `Potassium` tops out at `100` compared to `simulator.py`'s `180` baseline. Runtime safeguards in `backend/app/ml/fertilizer_model.py` (`SCIENTIFIC_CROP_MAP` mapping 15 of 22 crop labels and `VALID_FERTILIZER_SOIL_TEXTURES` withholding `Alluvial` without `confirmed_texture`) appropriately block out-of-schema predictions, but cannot fix the underlying synthetic rule bias.

---

### 4.3 Model C — Soil Image Classification (`MobileNetV2` CNN)

![Soil Classification MobileNetV2 Fresh Holdout & Training Curves](file:///D:/minor%201/Agrosmart/docs/model_evaluation/soil_cnn_evaluation.png)

* **Architecture & Parameters:** Pretrained ImageNet `MobileNetV2` backbone (`include_top=False`) + `GlobalAveragePooling2D` + `Dropout(0.3)` + `Dense(128, activation="relu")` + `Dropout(0.2)` + `Dense(4, activation="softmax")`. Total `2,422,468` parameters (`164,484` saved trainable, `2,257,984` non-trainable).
* **Two-Stage Training Trajectory (`soil_cnn_metrics.json`):**
  * **Stage 1 (Head training, backbone frozen, `lr=1e-3`, `9` epochs ran):** Improved rapidly from Epoch 1 (`train_acc=0.5118`, `loss=1.3409`; `val_acc=0.6832`, `val_loss=0.7494`) to best validation loss at **Epoch 5** (`val_loss=0.3713`, `val_acc=0.8614`, `train_acc=0.8480`, `train_loss=0.4029`), before plateauing/diverging slightly through Epoch 9 (`train_acc=0.9101`, `val_loss=0.4134`, `val_acc=0.8614`).
  * **Stage 2 (Fine-tuning top 20 layers with BatchNorm frozen, `lr=1e-4`, `5` epochs ran):** Training accuracy rose (`0.8694 -> 0.9208`) and training loss dropped (`0.4062 -> 0.2103`), while `val_loss` degraded (`0.3939 -> 0.4334 -> 0.4232`) and `val_acc` declined (`0.8614 -> 0.8317`). `ModelCheckpoint(monitor="val_loss")` successfully rejected Stage 2 overfitting and retained **Stage 1 Epoch 5** weights.
* **Fresh Evaluation of Saved Artifact (`soil_cnn_v1.h5` against `soil_cnn_splits.json`):**
  * **Train (unaugmented, `n=467`):** Loss `0.2722` | Accuracy `0.8972` (`89.72%`)
  * **Validation (`n=101`):** Loss `0.3713` | Accuracy `0.8614` (`86.14%`)
  * **Held-Out Test (`n=101`):** Loss `0.3692` | Accuracy **`0.9010`** (`90.10%`, `91/101` correct)
  * **Macro Precision / Recall / F1:** `0.9132` / `0.8756` / **`0.8882`**
  * **Weighted Precision / Recall / F1:** `0.9032` / `0.9010` / `0.8971`
* **Held-Out Test Confusion Matrix & Per-Class Metrics (`n = 101`):**

| True \ Predicted | `Alluvial` | `Black` | `Clay` | `Red` | Support | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`Alluvial`** | **`41`** | `1` | `0` | `1` | `43` | `0.8723` | `0.9535` | `0.9111` |
| **`Black`** | `4` | **`12`** | `1` | `1` | `18` | `0.9231` | **`0.6667`** | **`0.7742`** |
| **`Clay`** | `2` | `0` | **`15`** | `0` | `17` | `0.9375` | `0.8824` | `0.9091` |
| **`Red`** | `0` | `0` | `0` | **`23`** | `23` | `0.9200` | `1.0000` | `0.9583` |

* **Preprocessing, Augmentation & Runtime Parity Audit:**
  * Both training (`train_soil_cnn.py`) and runtime (`image_service.py` lines 120 & 128) rescale RGB pixel values to **`[-1, 1]`** matching `mobilenet_v2.preprocess_input`. However, docstring `image_service.py:10` and `docs/ml-pipeline.md` falsely document `[0, 1]` normalization.
  * Because `cv2` (`opencv-python-headless`) is missing from the active `.venv` despite appearing in `requirements.txt`, runtime uses Pillow `Image.LANCZOS` instead of Keras `bilinear` resizing. Fresh verification showed Pillow `LANCZOS` achieves identical `0.9010` test accuracy with `94.06%` (`95/101`) sample-level prediction agreement.
  * **Leaky `evaluate_models.py` CNN Branch:** `evaluate_models.py` (`lines 186–198`) ignores `soil_cnn_splits.json` and runs `ImageDataGenerator(validation_split=0.2, seed=42)` over the entire `soil_images/` folder, evaluating on an 80/20 random subset overlapping with training samples.
  * **Downstream Soil-Type Mismatch:** `recommendation_service.py` (`_SOIL_MODIFIER`) only defines irrigation modifiers for `Sandy`, `Loamy`, `Silty`, and `Clay`; CNN predictions of `Alluvial`, `Black`, and `Red` all silently fall back to `0.0`.

---

## 5. Cross-Model Comparison & Summary

![AgroSmart Phase 6 Cross-Model Audit & Readiness Comparison](file:///D:/minor%201/Agrosmart/docs/model_evaluation/model_comparison_summary.png)

1. **Strongest Current Model (Grounded in Real Data):** **Soil CNN (`MobileNetV2`)** — `90.10%` test accuracy (`0.8882` Macro F1) on authentic field/web soil imagery, though overstated by near-duplicate images across splits. **Crop RF** scores higher mathematically (`98.86%` test / `99.36%` CV-5), but exclusively against synthetic uniform data.
2. **Greatest Overfitting & Validity Risk:** **Fertilizer Decision Tree** exhibits complete feature validity failure (`crop_type`, `temperature`, `humidity` weight = `0.0000`) and weakest minority recall (`10-26-26` recall `72.73%`), while memorizing synthetic rules. In neural training, **Soil CNN Stage 2** demonstrated real-data fine-tuning overfitting (`val_loss` climbing `0.3939 -> 0.4232`), caught only by `ModelCheckpoint`.
3. **Priority Order for Upgrades:** (1) Replace synthetic Fertilizer & Crop CSVs with real agronomic datasets and align simulator ranges/fields; (2) Perceptually deduplicate `soil_images/` before re-splitting and address `Black` soil recall (`66.67%`).

---

## 6. Consolidated Problems Discovered

| Severity | Component | Finding |
| :--- | :--- | :--- |
| **CRITICAL** | Fertilizer Dataset & DT | 100% synthetic rule table; `Crop Type`, `Temperature`, `Humidity` ignored (`0.0000` importance); unsafe for field dosing. |
| **CRITICAL** | Crop Dataset & Simulator | 100% synthetic uniform boxes (`crop_matches_synthetic_generator_exactly: true`); simulator `K=180` exceeds training max `89.69` and forces constant `rainfall=52.0` fallback on `#1` feature (`0.2474` weight). |
| **HIGH** | Soil CNN Split Leakage | `70` exact perceptual dHash collisions (`hamming_dist == 0`) and `299` near-duplicates (`<= 4`) across Train/Val/Test despite `0` MD5 overlap; inflates held-out accuracy. |
| **HIGH** | `evaluate_models.py` | `evaluate_cnn_model()` uses random `validation_split=0.2` over all images instead of `soil_cnn_splits.json`, leaking training data into validation metrics. |
| **MEDIUM** | Soil CNN Class Balance & `.webp` | `Black` test recall is only `66.67%` (`4/18` misclassified as majority `Alluvial`); `2` `.webp` train images were silently skipped by `ImageDataGenerator`. |
| **MEDIUM** | Preprocessing & Script Leakage | `train_crop_model.py` & `train_fertilizer_model.py` scale/encode before CV (`line 106`/`130`) and re-fit scaler in `print_metrics()` (`line 168`); `StandardScaler` applied to nominal `LabelEncoder` integers. |
| **LOW** | Docs & Runtime Drift | `docs/ml-pipeline.md`, `datasets/README.md`, and `image_service.py:10` misstate CNN classes (`Sandy/Clay/Loamy/Silty`), `[-1, 1]` scaling (`[0, 1]`), and Kaggle provenance; `recommendation_service.py` lacks `_SOIL_MODIFIER` entries for `Alluvial`/`Black`/`Red`; `requirements.txt` mismatches `.venv` (`tensorflow 2.21.0`, missing `cv2`). |

---

## 7. Prioritized Phase 6 Improvement Roadmap

1. **Replace Synthetic Tabular Datasets (Crop & Fertilizer):** Acquire genuine Kaggle/agronomic datasets (e.g., authentic 2,200-row Crop Recommendation CSV and real multi-factor Fertilizer/soil nutrition datasets), harmonize sensor feature units (`K` scale, `rainfall` provenance), and replace nominal `LabelEncoder` + `StandardScaler` with `OneHotEncoder` inside scikit-learn `Pipeline`/`ColumnTransformer`.
2. **Deduplicate Soil Images & Re-Split Before Fine-Tuning:** Cluster near-duplicate images via perceptual `dHash`/`pHash` before stratified group splitting (`StratifiedGroupKFold` or clustered 70/15/15 split), convert `.webp` files to RGB `.jpg`/`.png` (replacing deprecated `ImageDataGenerator` with `tf.keras.utils.image_dataset_from_directory`), and apply class weights or focal loss to raise `Black` soil recall above `85%`.
3. **Fix Evaluation Script Integrity & Documentation Sync:** Update `evaluate_models.py` to evaluate exclusively against locked test splits (`soil_cnn_splits.json`), fix `CrossValidation` pipelines in `train_crop_model.py` / `train_fertilizer_model.py`, expand `_SOIL_MODIFIER` in `recommendation_service.py` for `Alluvial`/`Black`/`Red`, and synchronize `docs/ml-pipeline.md`, `image_service.py` docstrings, and `requirements.txt`.
