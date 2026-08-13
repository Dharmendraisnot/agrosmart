"""
generate_synthetic_datasets.py
Generates synthetic crop and fertilizer datasets that exactly mirror
the Kaggle CSV schemas. Used for development/testing when real datasets
have not yet been downloaded.

Run from backend/:
    python ml_training/generate_synthetic_datasets.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
DATASETS_DIR = Path(__file__).parent / "datasets"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)


# ── Crop Recommendation Dataset  (mirrors Kaggle schema exactly) ──────────────
def generate_crop_dataset():
    crops = [
        "rice", "maize", "chickpea", "kidneybeans", "pigeonpeas",
        "mothbeans", "mungbean", "blackgram", "lentil", "pomegranate",
        "banana", "mango", "grapes", "watermelon", "muskmelon",
        "apple", "orange", "papaya", "coconut", "cotton", "jute", "coffee",
    ]
    # Per-crop agronomic ranges: N, P, K, temperature, humidity, ph, rainfall
    params = {
        "rice":        ((60,100),(30,60),(30,60),(20,27),(80,90),(5.5,7.0),(200,300)),
        "maize":       ((60,100),(30,60),(30,60),(18,28),(55,75),(5.5,7.5),(60,110)),
        "chickpea":    ((30,50),(50,80),(60,90),(15,25),(15,25),(5.5,7.0),(60,80)),
        "kidneybeans": ((15,30),(50,80),(15,25),(15,25),(15,30),(5.5,7.0),(80,120)),
        "pigeonpeas":  ((15,25),(40,70),(15,25),(20,35),(30,60),(5.0,7.0),(60,90)),
        "mothbeans":   ((15,25),(30,55),(25,45),(25,35),(25,40),(3.5,6.5),(30,50)),
        "mungbean":    ((15,25),(30,55),(15,30),(25,35),(35,60),(6.0,7.0),(50,70)),
        "blackgram":   ((15,25),(50,80),(15,30),(25,35),(60,80),(6.0,7.5),(60,80)),
        "lentil":      ((15,25),(50,80),(15,30),(15,25),(60,70),(6.0,8.0),(35,50)),
        "pomegranate": ((15,25),(40,70),(15,30),(18,28),(80,95),(5.5,7.0),(100,130)),
        "banana":      ((80,120),(60,90),(40,70),(25,35),(75,90),(5.5,6.5),(100,150)),
        "mango":       ((15,25),(10,30),(25,45),(27,35),(50,65),(5.5,7.5),(90,110)),
        "grapes":      ((15,25),(10,30),(25,45),(8,38),(80,90),(5.5,6.5),(60,80)),
        "watermelon":  ((80,120),(10,30),(40,70),(25,35),(80,90),(5.5,7.0),(50,65)),
        "muskmelon":   ((80,120),(10,30),(40,70),(28,38),(90,95),(6.0,7.0),(20,30)),
        "apple":       ((0,20),(40,70),(25,45),(21,24),(90,95),(5.5,6.5),(100,120)),
        "orange":      ((0,20),(10,30),(5,15),(10,30),(90,95),(6.0,7.5),(100,120)),
        "papaya":      ((40,60),(10,30),(40,70),(25,35),(90,95),(6.5,7.5),(140,160)),
        "coconut":     ((0,20),(0,20),(25,45),(27,37),(85,95),(5.0,8.0),(140,160)),
        "cotton":      ((100,140),(10,30),(15,25),(21,30),(55,65),(6.0,8.0),(60,80)),
        "jute":        ((60,80),(40,60),(40,60),(24,37),(70,90),(6.0,8.0),(150,180)),
        "coffee":      ((80,120),(30,50),(25,45),(15,28),(90,95),(6.0,6.5),(150,250)),
    }

    rows = []
    for crop in crops:
        N_r, P_r, K_r, t_r, h_r, ph_r, rain_r = params[crop]
        for _ in range(100):
            rows.append({
                "N":           round(float(rng.uniform(*N_r)),   2),
                "P":           round(float(rng.uniform(*P_r)),   2),
                "K":           round(float(rng.uniform(*K_r)),   2),
                "temperature": round(float(rng.uniform(*t_r)),   2),
                "humidity":    round(float(rng.uniform(*h_r)),   2),
                "ph":          round(float(rng.uniform(*ph_r)),  2),
                "rainfall":    round(float(rng.uniform(*rain_r)),2),
                "label":       crop,
            })

    df = pd.DataFrame(rows)
    out = DATASETS_DIR / "crop_recommendation.csv"
    df.to_csv(out, index=False)
    print(f"Crop dataset saved: {len(df)} rows, {df['label'].nunique()} classes -> {out}")
    return df


# ── Fertilizer Prediction Dataset  (mirrors Kaggle schema exactly) ────────────
def generate_fertilizer_dataset():
    soil_types = ["Sandy", "Loamy", "Black", "Red", "Clayey"]
    crop_types = ["Wheat", "Tobacco", "Paddy", "Oil seeds", "Millets",
                  "Barley", "Cotton", "Ground Nuts", "Sugarcane", "Pulses",
                  "Maize", "Kidneybeans"]
    fertilizers = ["Urea", "DAP", "14-35-14", "28-28", "17-17-17",
                   "20-20", "10-26-26"]

    rows = []
    for _ in range(1000):
        temp     = round(float(rng.uniform(15, 40)), 1)
        humidity = round(float(rng.uniform(30, 90)), 1)
        moisture = round(float(rng.uniform(20, 80)), 1)
        soil     = rng.choice(soil_types)
        crop     = rng.choice(crop_types)
        nitrogen = round(float(rng.uniform(0, 120)), 1)
        potassium= round(float(rng.uniform(0, 100)), 1)
        phosphorus=round(float(rng.uniform(0, 100)), 1)

        # Simple deterministic rule to assign a fertilizer label
        # (mirrors the logic in the real Kaggle dataset patterns)
        if nitrogen < 20:
            fert = "Urea"
        elif phosphorus < 15:
            fert = "DAP"
        elif potassium < 20:
            fert = "28-28"
        elif nitrogen > 80 and phosphorus > 80:
            fert = "10-26-26"
        elif moisture < 30:
            fert = "20-20"
        elif soil in ("Sandy", "Red"):
            fert = "14-35-14"
        else:
            fert = "17-17-17"

        rows.append({
            "Temperature":    temp,
            "Humidity":       humidity,
            "Moisture":       moisture,
            "Soil Type":      soil,
            "Crop Type":      crop,
            "Nitrogen":       nitrogen,
            "Potassium":      potassium,
            "Phosphorous":    phosphorus,
            "Fertilizer Name": fert,
        })

    df = pd.DataFrame(rows)
    out = DATASETS_DIR / "fertilizer_recommendation.csv"
    df.to_csv(out, index=False)
    print(f"Fertilizer dataset saved: {len(df)} rows, {df['Fertilizer Name'].nunique()} classes -> {out}")
    return df


if __name__ == "__main__":
    generate_crop_dataset()
    generate_fertilizer_dataset()
    print("Synthetic datasets generated successfully.")
