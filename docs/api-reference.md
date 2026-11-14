# AgroSmart — REST API Specification & Reference

**Base URL:** `http://localhost:5000/api`
**Protocol:** HTTP/1.1
**Content-Type:** `application/json` (unless specifying `multipart/form-data` for image upload)
**Timestamp Format:** ISO 8601 UTC (`YYYY-MM-DDTHH:MM:SS.ffffff`)

---

## 1. Global Response & Error Handling Conventions

All endpoints adhere to standardized HTTP status codes and JSON response formats.

### Global Error Response Format (Phase 5 / S2 Pattern)
When an API error occurs (404, 405, 413, 422, or 500), the response returns a consistent JSON envelope with internal server tracebacks suppressed:

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource was not found on the server."
  }
}
```

#### Standard Error Codes:
* `BAD_REQUEST` (HTTP 400): Malformed JSON body or missing required field.
* `NOT_FOUND` (HTTP 404): The requested resource ID or URL does not exist.
* `METHOD_NOT_ALLOWED` (HTTP 405): HTTP method not supported on the specified endpoint.
* `PAYLOAD_TOO_LARGE` (HTTP 413): File upload exceeds the 10 MB limit.
* `VALIDATION_ERROR` (HTTP 422): Input field failed schema validation (e.g. non-numeric sensor reading).
* `INTERNAL_ERROR` (HTTP 500): Unhandled exception caught; sanitized generic message returned to client while full traceback is logged server-side.

---

## 2. Health & System Status

### `GET /api/health`
Checks backend system availability, database connectivity, and active sensor mode.

* **Method:** `GET`
* **Headers:** None
* **Query Parameters:** None
* **Response 200 (OK):**
  ```json
  {
    "status": "ok",
    "service": "AgroSmart API",
    "version": "1.0.0",
    "environment": "development",
    "sensor_mode": "simulator"
  }
  ```

---

## 3. Sensor Telemetry Endpoints

### `GET /api/sensors/latest`
Captures a fresh sensor reading snapshot from the hardware abstraction layer (HAL) and records it to the SQLite database.

* **Method:** `GET`
* **Response 200 (OK):**
  ```json
  {
    "id": 142,
    "timestamp": "2026-11-14T09:30:00.123456",
    "source": "simulator",
    "moisture": 52.3,
    "rainfall": 115.0,
    "ph": 6.65,
    "soil_temperature": 24.2,
    "air_temperature": 29.8,
    "air_humidity": 68.4,
    "nitrogen": 42.0,
    "phosphorus": 22.5,
    "potassium": 178.0
  }
  ```

---

### `GET /api/sensors/history`
Retrieves a paginated list of past sensor readings in descending chronological order (newest first).

* **Method:** `GET`
* **Query Parameters:**
  | Parameter | Type | Default | Constraints | Description |
  | :--- | :---: | :---: | :---: | :--- |
  | `page` | `int` | `1` | $\ge 1$ | Target page number |
  | `per_page` | `int` | `50` | $1 \le \text{per\_page} \le 200$ | Number of records per page |
* **Response 200 (OK):**
  ```json
  {
    "items": [
      {
        "id": 142,
        "timestamp": "2026-11-14T09:30:00.123456",
        "source": "simulator",
        "moisture": 52.3,
        "rainfall": 115.0,
        "ph": 6.65,
        "soil_temperature": 24.2,
        "air_temperature": 29.8,
        "air_humidity": 68.4,
        "nitrogen": 42.0,
        "phosphorus": 22.5,
        "potassium": 178.0
      }
    ],
    "total": 142,
    "page": 1,
    "per_page": 50,
    "pages": 3
  }
  ```

---

### `POST /api/sensors/reading`
Manually submits a custom sensor reading into the system without triggering the hardware simulator.

* **Method:** `POST`
* **Request Headers:** `Content-Type: application/json`
* **Request Body:**
  ```json
  {
    "source": "manual",
    "moisture": 48.0,
    "rainfall": 120.0,
    "ph": 6.8,
    "soil_temperature": 24.0,
    "air_temperature": 30.5,
    "air_humidity": 62.0,
    "nitrogen": 45.0,
    "phosphorus": 25.0,
    "potassium": 180.0
  }
  ```
  *(All fields optional; unsupplied fields stored as `null`).*
* **Response 201 (Created):** Returns the persisted `SensorReading` record.
* **Response 400 (Bad Request):** If request body is empty or not valid JSON.
* **Response 422 (Unprocessable Entity):** If any numeric field contains non-numeric data.

---

## 4. Soil Analysis & AI Orchestration

### `POST /api/analysis/run`
Executes the unified multi-modal AI decision pipeline:
1. Ingests telemetry: reads specified `reading_id`, or parses manual `sensor_data` (8 parameters), or triggers fresh HAL simulation.
2. Resolves soil type: classifies uploaded `image_path` via MobileNetV2 CNN, or accepts manual `soil_type`, or applies agronomic heuristic.
3. Calculates Soil Health Score (0–100) and condition classification ("Poor", "Fair", "Good").
4. Executes Crop Recommendation Random Forest model $\rightarrow$ top-3 ranked crop suggestions with confidence probabilities.
5. Executes Fertilizer Recommendation Decision Tree $\rightarrow$ nutrient deficiency advice (enforcing the Alluvial soil texture safeguard).
6. Executes Smart Irrigation Rule Engine $\rightarrow$ water requirements in $L/m^2$ and schedule urgency badge.
7. Persists `SoilAnalysis` session and linked `Prediction` records in a single transactional unit.

* **Method:** `POST`
* **Request Headers:** `Content-Type: application/json`
* **Request Body Parameters:**
  | Parameter | Type | Required? | Description |
  | :--- | :---: | :---: | :--- |
  | `reading_id` | `int` | Optional | ID of an existing `SensorReading` to analyze |
  | `sensor_data` | `dict` | Optional | Manual 9-parameter soil and environmental inputs (overrides hardware) |
  | `sensor_data.nitrogen` | `float` | Optional | Soil Nitrogen content ($N$) in $mg/kg$ |
  | `sensor_data.phosphorus` | `float` | Optional | Soil Phosphorus content ($P$) in $mg/kg$ |
  | `sensor_data.potassium` | `float` | Optional | Soil Potassium content ($K$) in $mg/kg$ |
  | `sensor_data.ph` | `float` | Optional | Soil pH level ($0.0$ to $14.0$) |
  | `sensor_data.moisture` | `float` | Optional | Soil moisture content ($0.0$ to $100.0\%$) |
  | `sensor_data.rainfall` | `float` | Optional | Rainfall in $mm$ |
  | `sensor_data.soil_temperature` | `float` | Optional | Soil temperature in $^\circ C$ |
  | `sensor_data.temperature` | `float` | Optional | Air temperature in $^\circ C$ (alias: `air_temperature`) |
  | `sensor_data.humidity` | `float` | Optional | Relative humidity in $\%$ (alias: `air_humidity`) |
  | `soil_type` | `string` | Optional | Explicit soil type override (`"Alluvial"`, `"Black"`, `"Clay"`, `"Red"`, `"Sandy"`, `"Loamy"`) |
  | `confirmed_soil_texture` | `string` | Optional | Mechanical soil texture confirmation (`"Sandy"`, `"Loamy"`, `"Silty"`, `"Clay"`, `"Clayey"`) |
  | `image_path` | `string` | Optional | Relative path or filename of previously uploaded soil image |
  | `notes` | `string` | Optional | User annotations or field observations |

* **Sample Request Body:**
  ```json
  {
    "sensor_data": {
      "nitrogen": 45.0,
      "phosphorus": 28.0,
      "potassium": 165.0,
      "ph": 6.5,
      "moisture": 54.0,
      "rainfall": 125.0,
      "air_temperature": 28.5,
      "air_humidity": 65.0
    },
    "soil_type": "Alluvial",
    "confirmed_soil_texture": "Loamy",
    "image_path": "uploads/sample_soil.jpg"
  }
  ```

* **Response 200 (OK):**
  ```json
  {
    "analysis_id": 18,
    "timestamp": "2026-11-14T09:35:12.654321",
    "sensor_reading": {
      "id": 143,
      "nitrogen": 45.0,
      "phosphorus": 28.0,
      "potassium": 165.0,
      "ph": 6.5,
      "moisture": 54.0,
      "rainfall": 125.0,
      "air_temperature": 28.5,
      "air_humidity": 65.0,
      "source": "manual"
    },
    "soil": {
      "type": "Alluvial",
      "type_confidence": 0.842,
      "health_status": "Good",
      "health_score": 92.5,
      "confirmed_soil_texture": "Loamy",
      "cnn_status": "ok"
    },
    "crops": [
      { "crop": "cotton", "confidence": 0.38, "rank": 1 },
      { "crop": "maize", "confidence": 0.31, "rank": 2 },
      { "crop": "jute", "confidence": 0.18, "rank": 3 }
    ],
    "fertilizer": {
      "fertilizer": "14-35-14",
      "advice": "Apply 14-35-14 at recommended dosage to balance phosphorus deficiency.",
      "model_label": "prototype_kaggle_v1.0",
      "soil_type": "Alluvial",
      "crop": "cotton"
    },
    "irrigation": {
      "action": "Monitor — soil moisture is adequate",
      "urgency": "medium",
      "frequency": "Every 2–3 days",
      "estimated_water": "15 L/m²",
      "effective_moisture": 54.0,
      "raw_moisture": 54.0,
      "temperature_note": null,
      "reasoning": "Effective moisture 54.0% is in the adequate range (40.0–60.0%)."
    },
    "prediction_ids": {
      "crop": 52,
      "fertilizer": 53,
      "irrigation": 54
    }
  }
  ```

* **Alluvial Soil Safeguard Behavior:**
  If `soil_type` is `"Alluvial"` and no `confirmed_soil_texture` is supplied, the fertilizer response is withheld to protect against spurious recommendations:
  ```json
  "fertilizer": {
    "fertilizer": "Reliable recommendation unavailable",
    "advice": "Alluvial soils vary from sandy loam to silty clay. Please confirm physical soil texture.",
    "status": "unsupported"
  }
  ```

---

### `GET /api/analysis/<id>`
Fetches complete analysis details and embedded prediction records for a specific session.

* **Method:** `GET`
* **Path Parameter:** `id` (`int`) — Analysis session ID.
* **Response 200 (OK):** Returns complete analysis dictionary.
* **Response 404 (Not Found):** If analysis ID does not exist.

---

### `GET /api/analysis/history`
Fetches paginated historical soil analysis sessions.

* **Method:** `GET`
* **Query Parameters:** `page` (`int`, default: 1), `per_page` (`int`, default: 20, max: 100).
* **Response 200 (OK):** Returns `{ items, total, page, per_page, pages }`.

---

## 5. Machine Learning Prediction Endpoints

### `GET /api/predictions/latest`
Fetches the three prediction records (`crop`, `fertilizer`, `irrigation`) generated during the most recent analysis session.

* **Method:** `GET`
* **Response 200 (OK):**
  ```json
  {
    "analysis_id": 18,
    "timestamp": "2026-11-14T09:35:12.654321",
    "soil": {
      "type": "Alluvial",
      "health_status": "Good",
      "health_score": 92.5
    },
    "predictions": {
      "crop": {
        "id": 52,
        "prediction_type": "crop",
        "result": { "crops": [ ... ] },
        "confidence": 0.38,
        "notes": "rf_v1"
      },
      "fertilizer": {
        "id": 53,
        "prediction_type": "fertilizer",
        "result": { "fertilizer": "14-35-14", ... },
        "confidence": null,
        "notes": "prototype_kaggle_v1.0"
      },
      "irrigation": {
        "id": 54,
        "prediction_type": "irrigation",
        "result": { "urgency": "medium", ... },
        "confidence": null,
        "notes": "rule_v1.0"
      }
    }
  }
  ```
* **Response 404 (Not Found):** If no analysis has been executed yet.

---

### `GET /api/predictions/<id>`
Retrieves a single prediction record by its primary key ID.

* **Method:** `GET`
* **Path Parameter:** `id` (`int`)
* **Response 200 (OK):** Returns prediction record with full deserialized result JSON.
* **Response 404 (Not Found):** If prediction record ID does not exist.

---

### `GET /api/predictions/history`
Retrieves a paginated list of all stored predictions, with optional filtering by prediction type.

* **Method:** `GET`
* **Query Parameters:**
  | Parameter | Type | Default | Description |
  | :--- | :---: | :---: | :--- |
  | `page` | `int` | `1` | Target page number |
  | `per_page` | `int` | `20` | Records per page (max: 100) |
  | `prediction_type` | `string` | Optional | Filter by `"crop"`, `"fertilizer"`, or `"irrigation"` |
* **Response 200 (OK):** Paginated items array.

---

## 6. Soil Image Classification Endpoints

### `POST /api/images/upload`
Uploads a soil photograph, validates format and dimensions, normalizes pixels to $[-1, 1]$, and executes inference using the active MobileNetV2 CNN (`soil_cnn_v1.h5`).

* **Method:** `POST`
* **Request Encoding:** `multipart/form-data`
* **Form Fields:**
  * `image` (File, Required): Soil photograph (`.jpg`, `.jpeg`, `.png`, `.webp`, maximum size 10 MB).
  * `run_analysis` (string, Optional): If `"true"` or `"1"`, triggers full analysis pipeline in the same request.
  * `confirmed_soil_texture` (string, Optional): User-confirmed texture if soil is Alluvial.

* **Response 200 (OK):**
  ```json
  {
    "filename": "f48c21a93e8749c98bc01d819e91244e_field_soil.jpg",
    "relative_path": "f48c21a93e8749c98bc01d819e91244e_field_soil.jpg",
    "soil_type": "Black",
    "confidence": 0.884,
    "all_classes": [
      { "class": "Black", "confidence": 0.884 },
      { "class": "Red", "confidence": 0.082 },
      { "class": "Alluvial", "confidence": 0.024 },
      { "class": "Clay", "confidence": 0.010 }
    ],
    "cnn_status": "ok"
  }
  ```

* **Possible `cnn_status` Values:**
  * `"ok"`: Inference successful.
  * `"model_unavailable"`: Model weights missing; heuristic fallback activated.
  * `"preprocessing_failed"`: Image corrupted or could not be decoded.

* **Response 400 (Bad Request):** Missing `image` file part.
* **Response 413 (Payload Too Large):** File exceeds 10 MB.
* **Response 422 (Unprocessable Entity):** Disallowed file extension or MIME spoofing detected.

---

### `GET /api/images/<filename>`
Serves an uploaded soil photograph by its unique safe filename.

* **Method:** `GET`
* **Path Parameter:** `filename` (`string`) — Sanitized image filename.
* **Security:** Directory traversal patterns (`..`, `/`, `\`) are strictly blocked.
* **Response 200 (OK):** Binary image stream with correct `Content-Type`.
* **Response 404 (Not Found):** File does not exist or invalid filename format.

---
*End of API Reference.*
