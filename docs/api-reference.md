# AgroSmart — API Reference

Base URL: `http://localhost:5000/api`

All responses are JSON. All timestamps are ISO 8601 UTC.

---

## Health

### `GET /api/health`
Returns system status and current sensor mode.

**Response 200**
```json
{
  "status":      "ok",
  "service":     "AgroSmart API",
  "version":     "1.0.0",
  "sensor_mode": "simulator",
  "environment": "development"
}
```

---

## Sensors

### `GET /api/sensors/latest`
Triggers a fresh sensor read (simulator or hardware) and persists to DB.

**Response 200**
```json
{
  "id": 42,
  "timestamp": "2025-08-01T10:30:00.000000",
  "source": "simulator",
  "moisture": 52.3,
  "ph": 6.5,
  "soil_temperature": 24.1,
  "air_temperature": 30.2,
  "air_humidity": 65.0,
  "nitrogen": 40.5,
  "phosphorus": 20.1,
  "potassium": 181.3
}
```

---

### `GET /api/sensors/history`
Paginated history of past sensor readings (newest first).

**Query parameters**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 50 | Items per page (max 200) |

**Response 200**
```json
{
  "items":    [ ...sensor reading objects... ],
  "total":    128,
  "page":     1,
  "per_page": 50,
  "pages":    3
}
```

---

### `POST /api/sensors/reading`
Manually submit a sensor reading (for testing or external injection).

**Request body** (all fields optional)
```json
{
  "moisture": 45.0,
  "ph": 6.8,
  "soil_temperature": 24.5,
  "air_temperature": 31.0,
  "air_humidity": 60.0,
  "nitrogen": 35.0,
  "phosphorus": 18.0,
  "potassium": 160.0,
  "source": "manual"
}
```

**Response 201** — the created reading object

**Error 400** — body is not JSON  
**Error 422** — a numeric field has a non-numeric value

---

## Analysis

### `POST /api/analysis/run`
Trigger the full AI analysis pipeline:
1. Reads sensors (HAL)
2. Runs CNN soil classification (if model available)
3. Computes soil health score
4. Runs Random Forest → top-3 crops
5. Runs Decision Tree → fertilizer advice
6. Runs rule engine → irrigation advice
7. Persists results to DB

**Request body** (optional)
```json
{ "reading_id": 42 }
```
Omit to capture a fresh reading.

**Response 200**
```json
{
  "analysis_id": 7,
  "timestamp": "2025-08-01T10:30:00",
  "sensor_reading": { ...sensor object... },
  "soil": {
    "type": "Loamy",
    "type_confidence": null,
    "health_status": "Good",
    "health_score": 87.5
  },
  "crops": [
    { "crop": "maize",  "confidence": 0.42, "rank": 1 },
    { "crop": "wheat",  "confidence": 0.28, "rank": 2 },
    { "crop": "cotton", "confidence": 0.14, "rank": 3 }
  ],
  "fertilizer": {
    "fertilizer":  "17-17-17",
    "advice":      "Apply 50 kg/acre...",
    "model_label": "prototype_kaggle_v1.0",
    "soil_type":   "Loamy",
    "crop":        "maize"
  },
  "irrigation": {
    "action":            "No irrigation needed",
    "urgency":           "low",
    "frequency":         "Check again in 3-4 days",
    "estimated_water":   "0 L/m²",
    "effective_moisture": 59.3,
    "raw_moisture":      58.0,
    "temperature_note":  null,
    "reasoning":         "Effective moisture 59.3% is good (60–75%)."
  },
  "prediction_ids": { "crop": 19, "fertilizer": 20, "irrigation": 21 }
}
```

**Error 404** — `reading_id` not found  
**Error 422** — `reading_id` is not a positive integer  
**Error 500** — pipeline error (detail in response)

---

### `GET /api/analysis/history`
Paginated analysis history (newest first).

**Query parameters** — `page`, `per_page` (max 100)

**Response 200** — paginated list with embedded predictions per analysis

---

### `GET /api/analysis/<id>`
Fetch one analysis record with embedded predictions.

**Response 200** — analysis object  
**Error 404** — not found

---

## Predictions

### `GET /api/predictions/latest`
Return the three prediction records from the most recent analysis.

**Response 200**
```json
{
  "analysis_id": 7,
  "timestamp": "2025-08-01T10:30:00",
  "soil": { "type": "Loamy", "health_status": "Good", "health_score": 87.5 },
  "predictions": {
    "crop":       { ...prediction object... },
    "fertilizer": { ...prediction object... },
    "irrigation": { ...prediction object... }
  }
}
```

**Error 404** — no analysis exists yet

---

### `GET /api/predictions/history`
Paginated prediction history.

**Query parameters**

| Param | Type | Description |
|-------|------|-------------|
| `page` | int | Page number |
| `per_page` | int | Items per page (max 100) |
| `prediction_type` | string | Filter: `crop` / `fertilizer` / `irrigation` |

---

### `GET /api/predictions/<id>`
Fetch one prediction record by ID.

**Response 200** — prediction object with `result` JSON embedded  
**Error 404** — not found

---

## Images

### `POST /api/images/upload`
Upload a soil image and run CNN classification.

**Request** — `multipart/form-data`, field name `image`  
**Accepted formats** — JPEG, PNG, WebP (max 10 MB, MIME-sniffed)

**Response 200**
```json
{
  "filename":      "a3f8...photo.jpg",
  "relative_path": "a3f8...photo.jpg",
  "soil_type":     "Loamy",
  "confidence":    0.87,
  "all_classes":   [
    { "class": "Loamy", "confidence": 0.87 },
    { "class": "Sandy", "confidence": 0.08 }
  ],
  "cnn_status":    "ok"
}
```

`cnn_status` values:
- `ok` — CNN model available and ran successfully
- `model_unavailable` — TensorFlow not installed or model file missing
- `preprocessing_failed` — image could not be decoded

**Error 400** — no `image` field  
**Error 422** — bad extension or MIME type mismatch

---

### `GET /api/images/<filename>`
Serve a previously uploaded image file.

**Response 200** — image file (Content-Type auto-detected)  
**Error 404** — file not found or path traversal attempt blocked
