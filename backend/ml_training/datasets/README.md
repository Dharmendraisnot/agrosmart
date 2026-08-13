# Datasets

Training datasets are **not** committed to version control due to file size.

## Crop Recommendation Dataset
- **Source:** [Kaggle — Crop Recommendation Dataset](https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset)
- **File name:** `crop_recommendation.csv`
- **Rows:** 2200 | **Classes:** 22 crops
- **Features:** N, P, K, temperature, humidity, ph, rainfall
- **Usage:** Train `crop_rf_v1.pkl` (Random Forest)

## Fertilizer Recommendation Dataset (Prototype)
- **Source:** [Kaggle — Fertilizer Prediction](https://www.kaggle.com/datasets/gdabhishek/fertilizer-prediction)
- **File name:** `fertilizer_recommendation.csv`
- **Usage:** Train `fertilizer_dt_prototype.pkl`
- **⚠ PROTOTYPE ONLY** — will be replaced by AgroSmart-collected data in Phase 5

## Soil Image Dataset (CNN)
- **Source:** Public soil type image dataset (search Kaggle: "soil type classification")
- **Directory:** `soil_images/` with subdirectories per class (Sandy/, Clay/, Loamy/, Silty/)
- **Usage:** Train `soil_cnn_v1.h5` (MobileNetV2 transfer learning)

## AgroSmart Collected Data (Phase 5+)
- Collected from real Raspberry Pi sensor readings during field testing
- Used to fine-tune crop model and replace the fertilizer prototype model
