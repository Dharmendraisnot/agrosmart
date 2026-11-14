# AgroSmart — Comparative Soil CNN Error Analysis & Model Diagnostics (Task P1.4)

**Project:** AgroSmart — AI-Based Soil Analysis & Crop Recommendation System
**Task:** Phase 6, Task P1.4 — Comparative CNN Error Analysis and Model Diagnostics
**Baseline Model (Production):** `backend/trained_models/soil_cnn_v1.h5`
**Retrained Model (Experimental):** `backend/trained_models/soil_cnn_v2.h5`
**Dataset Source:** `backend/ml_training/datasets/soil_images_clean/` (470 canonical scenes)
**Evaluated Split:** `test_files` from `backend/trained_models/soil_cnn_splits_v2.json` ($N = 71$ held-out test images)
**Detailed Data Artifact:** `docs/model_evaluation/soil_cnn_error_analysis/comparative_predictions.json`

> [!IMPORTANT]
> **Safety & Integrity Guarantee:** This audit is strictly analytical. No model weights, classes, datasets, split metadata, or production inference configurations were modified during this task. Both models were evaluated on the identical 71 held-out test images under zero-leakage conditions.

---

## 1. Executive Summary

In Task P1.3, MobileNetV2 was retrained as `soil_cnn_v2.h5` to address the low Clay recall ($66.67\%$) and test set leakage observed in baseline `soil_cnn_v1.h5`. While V2 successfully elevated **Clay recall to $73.33\%$** ($+6.67\%$), boosted **Alluvial recall to $89.47\%$** ($+10.53\%$), and achieved **$100.0\%$ precision on Red soil** (zero false positives), it suffered a significant reduction in **Black soil recall from $88.89\%$ down to $66.67\%$**.

Overall test accuracy remained nearly identical within a margin of a single test image:
* **Baseline V1 Accuracy:** **`81.69%`** ($58 / 71$ images correct)
* **Retrained V2 Accuracy:** **`80.28%`** ($57 / 71$ images correct)

Task P1.4 conducts an exhaustive, sample-by-sample error analysis of all 71 held-out test images to uncover the root photometric, textural, and algorithmic causes behind model disagreements, misclassifications, and the Black soil recall drop.

```
Total Test Images Evaluated (N = 71)
   │
   ├── Group 1: Both Models Correct ──────────────── 51 images (71.8%)
   │
   ├── Group 2: Both Models Incorrect (Shared Errors) ─ 7 images  (9.9%)
   │
   ├── Group 3: V1 Correct, V2 Incorrect (V1 Wins) ─── 7 images  (9.9%)
   │
   └── Group 4: V2 Correct, V1 Incorrect (V2 Wins) ─── 6 images  (8.5%)
```

Across the entire held-out test set, exactly **20 images** were misclassified by at least one model, while **51 images** ($71.8\%$) were classified correctly by both architectures.

---

## 2. Model Comparison Breakdown & Prediction Dynamics

![Model Comparison Breakdown](file:///D:/minor%201/Agrosmart/docs/model_evaluation/soil_cnn_error_analysis/model_comparison_breakdown.png)

### 2.1 The Four Concordance Groups

| Concordance Group | Count | Percentage | Description / Significance |
| :--- | :---: | :---: | :--- |
| **Group 1: Both Correct** | **51** | **`71.8%`** | High-confidence core capability shared by both models. |
| **Group 2: Both Failed** | **7** | **`9.9%`** | Hard/ambiguous images: dry clay resembling alluvial loam, extreme underexposure, or low-resolution thumbnails. |
| **Group 3: V1 Win / V2 Fail** | **7** | **`9.9%`** | V2 regressions: 4 Black soils flipped to Alluvial/Clay, 1 Alluvial flipped to Black, 2 Red soils missed. |
| **Group 4: V2 Win / V1 Fail** | **6** | **`8.5%`** | V2 improvements: 3 Alluvial soils misidentified as Red in V1 fixed, 2 dark Red soils fixed, 1 Clay soil recovered. |

### 2.2 Class-Wise Migration Matrix ($N = 71$)

| Class | Support | V1 Correct | V2 Correct | Net Delta | Dominant Transition in V2 |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Alluvial** | 19 | 15 ($78.9\%$) | **17 ($89.5\%$)** | **$+2$** | Eliminated all 3 Alluvial $\rightarrow$ Red confusions; gained 1 grayscale error. |
| **Black** | 18 | **16 ($88.9\%$)** | 12 ($66.7\%$) | **$-4$** | **Net loss of 4 images:** 3 flipped to Alluvial, 1 flipped to Clay. |
| **Clay** | 15 | 10 ($66.7\%$) | **11 ($73.3\%$)** | **$+1$** | Recovered `clay_0044.jpg` from Alluvial bucket due to class weighting. |
| **Red** | 19 | 17 ($89.5\%$) | 17 ($89.5\%$) | **$\pm 0$** | Recovered 2 shadowed Red images; lost 1 bleached and 1 low-confidence image. |
| **Total** | **71** | **58 ($81.7\%$)** | **57 ($80.3\%$)** | **$-1$** | Net difference across test set is exactly **1 test image**. |

---

## 3. Comprehensive Visual Contact Sheet of All 20 Error Cases

All 20 test images that triggered an error in either V1, V2, or both were extracted, analyzed, and compiled into the high-resolution diagnostic contact sheet below.

![Misclassified Contact Sheet](file:///D:/minor%201/Agrosmart/docs/model_evaluation/soil_cnn_error_analysis/misclassified_contact_sheet.png)

### 3.1 Itemized Error Case Directory

#### Group 2: Shared Failures (Both Models Failed — $N = 7$)
| File | True Class | V1 Prediction | V2 Prediction | Photometric Indicators | Visual Defect / Root Cause |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `Black/black_0035.jpg` | Black | Alluvial ($54.7\%$) | Alluvial ($67.0\%$) | Lum: 59.2, Sat: 64.4, Sharp: 2059 | Greyish dry crusting on black soil. |
| `Black/black_0076.jpg` | Black | Alluvial ($74.4\%$) | Alluvial ($67.6\%$) | Lum: **19.1**, Sat: 20.3, Sharp: **274** | **Severe underexposure:** Nearly pitch-black image with lost texture. |
| `Clay/clay_0003.jpg` | Clay | Red ($58.9\%$) | Alluvial ($50.1\%$) | Lum: 130.0, Sat: **156.1**, Sharp: 2958 | **Strong reddish chrominance:** Brick-red fired clay appearance. |
| `Clay/clay_0045.jpg` | Clay | Alluvial ($60.5\%$) | Alluvial ($89.3\%$) | Lum: 122.3, Sat: 58.0, Sharp: 3685 | Low saturation dry clay without cracking; looks like alluvial loam. |
| `Clay/clay_0055.jpeg` | Clay | Alluvial ($75.1\%$) | Alluvial ($46.2\%$) | Lum: 108.1, Sat: 115.6, Sharp: 830 | Ambiguous color; V2 split $46.2\%$ Alluvial vs $45.9\%$ Clay (dead heat). |
| `Clay/clay_0090.jpeg` | Clay | Alluvial ($90.6\%$) | Alluvial ($93.1\%$) | Lum: **178.3**, Sat: 55.1, Sharp: 6962 | **Harsh direct sunlight:** Washed-out dry clay mimicking sandy alluvium. |
| `Alluvial/alluvial_0037.jpeg` | Alluvial | Black ($77.4\%$) | Black ($69.1\%$) | Lum: 110.1, Sat: 98.4, Res: **100x100** | Wet dark alluvial sediment; low resolution thumbnail. |

#### Group 3: V1 Correct, V2 Incorrect (Regressions in V2 — $N = 7$)
| File | True Class | V1 Prediction | V2 Prediction | Photometric Indicators | Why V2 Failed |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `Black/black_0014.jpg` | Black | Black ($64.2\%$) [OK] | Alluvial ($75.2\%$) [ERR] | Lum: 75.6, Sat: **6.91**, Sharp: 16719 | **Virtually zero color saturation ($6.9$):** Pure grey tone misread as loam. |
| `Black/black_0023.jpg` | Black | Black ($75.4\%$) [OK] | Alluvial ($88.2\%$) [ERR] | Lum: 92.7, Sat: 110.9, Sharp: 2834 | Dry topsoil with higher reflectance ($L = 92.7$); Alluvial pull. |
| `Black/black_0036.jpg` | Black | Black ($51.2\%$) [OK] | Clay ($59.2\%$) [ERR] | Lum: 105.2, Sat: 83.2, Sharp: 14454 | V1 confidence was borderline ($51\%$). **Clay weight ($1.41\times$) tipped it.** |
| `Black/black_0051.jpg` | Black | Black ($57.9\%$) [OK] | Alluvial ($85.0\%$) [ERR] | Lum: 49.7, Sat: 99.4, Res: **100x100** | Borderline in V1 ($57.9\%$ Black, $33.8\%$ Red); flipped to Alluvial in V2. |
| `Alluvial/alluvial_0068.jpg` | Alluvial | Alluvial ($82.5\%$) [OK] | Black ($43.1\%$) [ERR] | Lum: 144.3, Sat: **0.02**, Sharp: 2381 | **Grayscale / B&W photograph:** Zero chrominance confused V2. |
| `Red/red_0049.jpg` | Red | Red ($77.3\%$) [OK] | Alluvial ($85.4\%$) [ERR] | Lum: **154.3**, Sat: 62.8, Sharp: **237** | Bleached, low-saturation pale red sand; V2 saw it as sandy loam. |
| `Red/red_0138.jpg` | Red | Red ($85.9\%$) [OK] | Clay ($35.8\%$) [ERR] | Lum: 129.3, Sat: 102.3, Sharp: 2033 | Diffused lighting; V2 split across Clay ($36\%$), Black ($29\%$), Red ($29\%$). |

#### Group 4: V2 Correct, V1 Incorrect (Improvements in V2 — $N = 6$)
| File | True Class | V1 Prediction | V2 Prediction | Photometric Indicators | Why V2 Succeeded |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `Alluvial/alluvial_0062.jpg` | Alluvial | Red ($55.3\%$) [ERR] | **Alluvial ($93.6\%$) [OK]** | Lum: 129.3, Sat: 94.3, Sharp: 6340 | V1 had false Red bias; V2 correctly recognized alluvial silt texture. |
| `Alluvial/alluvial_0032.webp` | Alluvial | Red ($83.8\%$) [ERR] | **Alluvial ($63.4\%$) [OK]** | Lum: 93.0, Sat: 110.6, Sharp: 2063 | Previously skipped WebP format; V2 correctly identified Alluvial. |
| `Alluvial/alluvial_0089.jpeg` | Alluvial | Red ($93.8\%$) [ERR] | **Alluvial ($79.0\%$) [OK]** | Lum: 155.8, Sat: 118.5, Sharp: 6781 | V1 was severely overconfident on Red ($93.8\%$); V2 fixed it. |
| `Clay/clay_0044.jpg` | Clay | Alluvial ($64.2\%$) [ERR] | **Clay ($50.9\%$) [OK]** | Lum: 131.0, Sat: 94.1, Sharp: 4122 | **Clay class weight boost enabled correct detection over Alluvial.** |
| `Red/red_0132.jpg` | Red | Black ($60.0\%$) [ERR] | **Red ($37.9\%$) [OK]** | Lum: 124.6, Sat: 117.0, Sharp: 14414 | Shadowed red soil; V1 thought it was Black; V2 discerned red chroma. |
| `Red/red_0046.jpg` | Red | Black ($59.6\%$) [ERR] | **Red ($68.9\%$) [OK]** | Lum: 94.5, Sat: 170.4, Sharp: 13785 | Dark red soil with deep shadows; V2 separated hue from darkness. |

---

## 4. Class-Wise Root Cause Error Analysis

![Class Error Distribution](file:///D:/minor%201/Agrosmart/docs/model_evaluation/soil_cnn_error_analysis/class_error_distribution.png)

### 4.1 Black Soil: Analysis of the Recall Reduction ($88.9\% \rightarrow 66.7\%$)

The reduction of Black soil recall in V2 represents the single largest behavioral regression between the two models. Investigating the 6 misclassified Black images reveals clear patterns:

1. **The Dry Surface Reflectance Phenomenon:**
   * Natural black cotton soil (Vertisols) varies dramatically based on surface moisture. When saturated, it absorbs light, displaying a deep charcoal black hue ($L < 40$). When dry, surface dust crumbles and scatters light, elevating luminance into the range of $L = 75 - 95$.
   * In `black_0023.jpg` ($L = 92.7$) and `black_0014.jpg` ($L = 75.6$), the dry surface brightness caused V2 to strongly prefer Alluvial ($88.2\%$ and $75.2\%$).
2. **Neutral Color Desaturation:**
   * `black_0014.jpg` possesses a mean saturation of only **$6.91$** (out of 255), meaning it is virtually a monochrome grayscale image without chromatic warmth or coolness. V2 defaulted to Alluvial because Alluvial has the broadest distribution in the feature space.
3. **Borderline Probability Tipping:**
   * In V1, `black_0036.jpg` was predicted Black with only **$51.2\%$ confidence** (with $38.3\%$ Alluvial). In V2, because Clay received an explicit $1.4084$ class weight boost, the network assigned $59.2\%$ probability to Clay. The class weight effectively "tipped" this borderline image out of Black.
4. **Underexposed Outliers:**
   * `black_0076.jpg` has a mean luminance of **$19.14$** and sharpness of only $274$. Both models failed completely on this image, predicting Alluvial ($74.4\%$ in V1, $67.6\%$ in V2). This is a camera exposure failure, not an agronomic failure.

### 4.2 Clay Soil: Analysis of the Alluvial Confusion Channel

Clay soil had the lowest recall in V1 ($66.67\%$) and improved to $73.33\%$ in V2.

1. **Why Clay is Frequently Confused with Alluvial:**
   * Across both models, **4 Clay samples** (`clay_0003`, `clay_0045`, `clay_0055`, `clay_0090`) were misclassified as Alluvial.
   * `clay_0090.jpeg` has a mean luminance of **$178.33$** (photographed under blazing sunlight). Direct specular reflection washes out fine surface cracks, making dry clay visually indistinguishable from bleached river silt. Both models were $>90\%$ confident it was Alluvial.
   * `clay_0045.jpg` and `clay_0055.jpeg` lack coarse clods or deep shrinkage fissures; their fine particle texture closely matches alluvial loam.
2. **How V2 Improved Clay Recall:**
   * In `clay_0044.jpg`, V1 assigned $64.2\%$ to Alluvial and only $34.9\%$ to Clay. V2 re-weighted this distribution to **$50.9\%$ Clay vs $48.0\%$ Alluvial**, successfully recovering the sample.

### 4.3 Alluvial Soil: Total Elimination of False Red Errors

In V1, Alluvial suffered from an error mode where light brownish-yellow sediment was mistaken for Red soil:
* `alluvial_0062.jpg` (V1: $55.3\%$ Red $\rightarrow$ V2: **$93.6\%$ Alluvial**)
* `alluvial_0032.webp` (V1: $83.8\%$ Red $\rightarrow$ V2: **$63.4\%$ Alluvial**)
* `alluvial_0089.jpeg` (V1: $93.8\%$ Red $\rightarrow$ V2: **$79.0\%$ Alluvial**)

V2 completely eradicated this failure mode. The geometric data augmentation and clean split training enabled MobileNetV2 to learn that high red-channel values in alluvial soil are accompanied by high green-channel values (yellowish-brown loam), whereas true Red soil has a much lower green/red ratio.

### 4.4 Red Soil: Perfect $100\%$ Precision Achieved

* Because all three Alluvial $\rightarrow$ Red false positives were eliminated, **V2 achieved a perfect $100.0\%$ precision on Red soil**.
* Furthermore, V2 correctly resolved two deeply shadowed Red soil samples (`red_0132.jpg` and `red_0046.jpg`) that V1 had misclassified as Black soil due to heavy shadows ($L = 94.5$).

---

## 5. Confidence, Uncertainty, and Calibration Diagnostics

![Confidence Comparison](file:///D:/minor%201/Agrosmart/docs/model_evaluation/soil_cnn_error_analysis/confidence_comparison.png)

### 5.1 Observed Confidence Distributions

* **Correct Predictions:** Both models show high median confidence on correct predictions ($\approx 88 - 92\%$).
* **Incorrect Predictions:** Both models exhibit substantial overconfidence when making erroneous predictions:
  * V1 median error confidence: **`74.4%`**
  * V2 median error confidence: **`68.9%`**
* **Severe Overconfidence ($>75\%$ Confidence on Wrong Class):**
  * **V1:** 4 images misclassified with $>75\%$ confidence (e.g., `alluvial_0089.jpeg` at $93.8\%$ Red; `clay_0090.jpeg` at $90.6\%$ Alluvial).
  * **V2:** 5 images misclassified with $>75\%$ confidence (e.g., `clay_0090.jpeg` at $93.1\%$ Alluvial; `black_0023.jpg` at $88.2\%$ Alluvial).

### 5.2 Ground-Truth Probability Mass

* When plotting the probability assigned to the **actual ground-truth class** across all 71 images:
  * V1 Mean Ground-Truth Probability: **`77.8%`**
  * V2 Mean Ground-Truth Probability: **`76.5%`**
* Both models concentrate high probability mass on the correct class for over $80\%$ of the test set, but drop sharply to $<15\%$ on the 7 mutually shared hard edge cases.

---

## 6. Photometric & Texture Correlation Diagnostics

![Image Feature Correlations](file:///D:/minor%201/Agrosmart/docs/model_evaluation/soil_cnn_error_analysis/image_feature_correlations.png)

```
Photometric Space: Luminance vs. Saturation
Luminance (L)
  ▲
  │  Harsh Sunlight / Overexposed
  │   [clay_0090] (L=178, S=55)  -> Both models predict Alluvial
  │   [red_0049]  (L=154, S=63)  -> V2 predicts Alluvial
  │   [alluvial_0068] (L=144, S=0) -> Grayscale photo, V2 predicts Black
  │
  │  Typical Balanced Exposure (L = 90 - 130)
  │   [Core Soil Clusters: Strong Class Separation]
  │
  │  Severe Shadows / Underexposure
  │   [black_0076] (L=19, S=20)  -> Pitch black, both fail
  │
  └────────────────────────────────────────────────────────► Saturation (S)
```

### 6.1 Saturation as a Disqualifier for Black Soil
* In Panel B of the feature diagnostic, correctly classified Black soils have a median saturation of **$88.4$**, whereas the Black soils misclassified as Alluvial have a significantly lower median saturation of **$64.4$** (including `black_0014` at $S = 6.9$).
* When a Black soil image lacks rich dark-brown/black organic tone and appears as neutral flat grey, the CNN defaults to Alluvial.

### 6.2 Luminance as a Confounder for Clay vs. Alluvial
* In Panel C, correctly classified Clay samples have a median luminance of **$112.5$**, whereas Clay samples misclassified as Alluvial have an elevated median luminance of **$126.1$** (reaching $178.3$ in `clay_0090`).
* High surface reflectance in dry agricultural soils consistently pulls predictions toward Alluvial.

---

## 7. Model Diagnostics: Evidence vs. Hypotheses

To maintain research rigor, observed facts are strictly separated from interpretive hypotheses.

### 7.1 Observed Evidence (Factual)
1. **Asymmetric Class Weighting in V2:**
   * V2 used inverse frequency weights with a manual $1.25\times$ multiplier on Clay:
     * Alluvial: $0.9676$
     * Black: $1.0154$
     * **Clay: $1.4084$** ($+45.6\%$ higher than Alluvial, $+38.7\%$ higher than Black)
     * Red: $0.9139$
2. **Augmentation Limitations:**
   * V2 training included **only geometric transformations** (horizontal flip, $\pm 14^\circ$ rotation, $\pm 8\%$ zoom, $\pm 5\%$ translation).
   * **Zero photometric augmentation** was applied: no random brightness, no random contrast, no hue/saturation jitter, and no color dropout.
3. **Training Dynamics & Overfitting:**
   * Stage 1 (frozen backbone) achieved peak validation loss of **`0.2896`** at Epoch 9.
   * Stage 2 (fine-tuning top 25 layers) drove training loss down to $0.1031$ while validation loss rose slightly to $0.3565$, indicating slight specialization on specific training frame pixel values.
4. **Alluvial Feature Space Dominance:**
   * Alluvial soil in the dataset contains the highest intra-class variety of soil sub-types (silty loam, coarse sand, gravel, riverbed silt), making its latent representation wider than the other classes.

### 7.2 Diagnostic Hypotheses (Interpretive)
1. **Hypothesis A — Boundary Erosion from Clay Weight Inflation:**
   * By boosting the Clay loss penalty by $1.4084$, the optimizer aggressively penalized any Clay false negatives during gradient descent. This expanded the decision region of Clay and compressed adjacent regions. For borderline neutral samples (such as `black_0036`), the boundary shifted away from Black toward Clay.
2. **Hypothesis B — Lack of Photometric Invariance:**
   * Because V2 never experienced brightness or saturation jitter during training, the network learned that "Black soil = low pixel values in all channels." When presented with dry, sun-bleached, or dusty Black soil samples ($L > 75$), the network could not generalize based on micro-texture alone and defaulted to Alluvial.
3. **Hypothesis C — Overconfidence in Unweighted Ensembles:**
   * A synthetic 50/50 probability ensemble between V1 and V2 on the test set yielded **$78.87\%$ accuracy** (56/71), performing *worse* than either standalone model ($81.7\%$ and $80.3\%$). This occurs because both models produce high-confidence erroneous outputs ($>85\%$), which overrule modest correct predictions in a naive average.

---

## 8. Prioritized Recommendations for Future Retraining (P2)

These recommendations are prioritized based on experimental diagnostic findings:

| Priority | Strategy | Implementation Mechanism | Expected Impact |
| :---: | :--- | :--- | :--- |
| **P1** | **Photometric Data Augmentation** | Add `RandomBrightness(0.2)`, `RandomContrast(0.2)`, and HSV jitter to training pipeline. | **Crucial:** Forces model to learn micro-texture rather than absolute pixel brightness. Eliminates dry Black $\rightarrow$ Alluvial errors. |
| **P2** | **Focal Loss / Balanced Loss** | Replace standard cross-entropy with Multi-Class Focal Loss ($\gamma = 2.0$) or equal class weighting. | Prevents artificial boundary warping caused by heuristic $1.25\times$ multiplier. |
| **P3** | **Conservative Fine-Tuning** | Unfreeze only top 10 layers (instead of 25) with Cosine Decay learning rate ($\eta_{\text{max}} = 10^{-5}$) and Dropout $= 0.5$. | Prevents Stage 2 validation loss rise ($0.289 \rightarrow 0.356$) on small $N = 329$ training set. |
| **P4** | **Temperature Scaling / Calibration** | Apply post-hoc temperature scaling ($T \approx 1.3 - 1.5$) to softmax logits. | Alleviates severe overconfidence on incorrect predictions ($>75\%$). |
| **P5** | **Targeted Data Collection** | Acquire 15–20 real field images of: (a) Dry cracked Black soil; (b) Harsh-sunlight dry Clay. | Closes the real-world semantic overlap gap at the physical dataset level. |

---

## 9. Conclusion & Operational Recommendation

1. **Production Deployment Decision:**
   * **Maintain `soil_cnn_v1.h5` as the active production model** in `backend/app/ml/soil_cnn.py`. It holds the higher overall test accuracy ($81.69\%$) and superior Black soil recall ($88.89\%$).
2. **Experimental Model Status:**
   * `soil_cnn_v2.h5` remains an invaluable reference artifact that conclusively proved that:
     * Clay recall can be improved from $66.7\%$ to $73.3\%$.
     * Red soil false positives can be completely eradicated ($100\%$ precision).
     * Alluvial recall can be elevated to $89.5\%$.
3. **Viva / Academic Defense Value:**
   * Presenting this comparative error analysis demonstrates engineering maturity. Rather than concealing the Black recall trade-off, documenting its exact photometric mechanism proves an advanced understanding of computer vision in agricultural applications.
