"""
test_api.py — Integration tests for all REST API endpoints.

Uses Flask test client with in-memory SQLite (TestingConfig).
Tests cover:
  - Health endpoint
  - Sensor endpoints (latest, history, manual submit)
  - Analysis endpoint (run, history, get by id)
  - Predictions endpoints (latest, history, get by id)
  - Images endpoints (upload, serve, validation, path traversal)
  - Error handling (bad inputs, not found)
"""
import io
import zlib
import struct
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_png() -> bytes:
    """Create a valid minimal 1×1 PNG for upload tests."""
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    sig  = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


# ── Health ────────────────────────────────────────────────────────────────────

class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200

    def test_health_returns_ok_status(self, client):
        d = client.get("/api/health").get_json()
        assert d["status"] == "ok"

    def test_health_returns_sensor_mode(self, client):
        d = client.get("/api/health").get_json()
        assert "sensor_mode" in d
        assert d["sensor_mode"] == "simulator"

    def test_health_returns_service_name(self, client):
        d = client.get("/api/health").get_json()
        assert d["service"] == "AgroSmart API"


# ── Sensors ───────────────────────────────────────────────────────────────────

class TestSensorEndpoints:

    def test_latest_returns_200(self, client):
        r = client.get("/api/sensors/latest")
        assert r.status_code == 200

    def test_latest_has_required_fields(self, client):
        d = client.get("/api/sensors/latest").get_json()
        required = {"id", "timestamp", "source", "moisture", "ph",
                    "soil_temperature", "air_temperature", "air_humidity",
                    "nitrogen", "phosphorus", "potassium"}
        assert required.issubset(set(d.keys()))

    def test_latest_source_is_simulator(self, client):
        d = client.get("/api/sensors/latest").get_json()
        assert d["source"] == "simulator"

    def test_latest_saves_to_db(self, client):
        d1 = client.get("/api/sensors/latest").get_json()
        d2 = client.get("/api/sensors/latest").get_json()
        assert d2["id"] > d1["id"]   # each call creates a new reading

    def test_history_returns_200(self, client):
        r = client.get("/api/sensors/history")
        assert r.status_code == 200

    def test_history_has_pagination_keys(self, client):
        d = client.get("/api/sensors/history").get_json()
        assert {"items", "total", "page", "per_page", "pages"}.issubset(set(d.keys()))

    def test_history_respects_per_page(self, client):
        # Create several readings first
        for _ in range(5):
            client.get("/api/sensors/latest")
        d = client.get("/api/sensors/history?per_page=2").get_json()
        assert len(d["items"]) <= 2

    def test_manual_submit_returns_201(self, client):
        r = client.post("/api/sensors/reading",
                        json={"moisture": 45.0, "ph": 6.8, "source": "test"})
        assert r.status_code == 201

    def test_manual_submit_stores_values(self, client):
        r = client.post("/api/sensors/reading",
                        json={"moisture": 42.5, "ph": 7.1, "nitrogen": 35.0})
        d = r.get_json()
        assert d["moisture"] == 42.5
        assert d["ph"] == 7.1

    def test_manual_submit_stores_rainfall(self, client):
        r = client.post("/api/sensors/reading",
                        json={"moisture": 42.5, "rainfall": 85.0, "nitrogen": 35.0})
        assert r.status_code == 201
        d = r.get_json()
        assert d["moisture"] == 42.5
        assert d["rainfall"] == 85.0

    def test_manual_submit_bad_type_returns_422(self, client):
        r = client.post("/api/sensors/reading",
                        json={"moisture": "not-a-number"})
        assert r.status_code == 422

    def test_manual_submit_no_body_returns_400(self, client):
        r = client.post("/api/sensors/reading",
                        data="not json",
                        content_type="text/plain")
        assert r.status_code == 400


# ── Analysis ──────────────────────────────────────────────────────────────────

class TestAnalysisEndpoints:

    def test_run_returns_200(self, client):
        r = client.post("/api/analysis/run")
        assert r.status_code == 200

    def test_run_result_structure(self, client):
        d = client.post("/api/analysis/run").get_json()
        assert "analysis_id"    in d
        assert "sensor_reading" in d
        assert "soil"           in d
        assert "crops"          in d
        assert "fertilizer"     in d
        assert "irrigation"     in d
        assert "prediction_ids" in d

    def test_run_soil_has_required_keys(self, client):
        d = client.post("/api/analysis/run").get_json()
        soil = d["soil"]
        assert "type"          in soil
        assert "health_status" in soil
        assert "health_score"  in soil

    def test_run_health_status_valid(self, client):
        d = client.post("/api/analysis/run").get_json()
        assert d["soil"]["health_status"] in ("Good", "Fair", "Poor")

    def test_run_health_score_in_range(self, client):
        d = client.post("/api/analysis/run").get_json()
        score = d["soil"]["health_score"]
        assert 0 <= score <= 100

    def test_run_crops_is_list_of_three(self, client):
        d = client.post("/api/analysis/run").get_json()
        assert isinstance(d["crops"], list)
        assert len(d["crops"]) == 3

    def test_run_crop_items_have_required_keys(self, client):
        d = client.post("/api/analysis/run").get_json()
        for crop in d["crops"]:
            assert {"crop", "confidence", "rank"}.issubset(set(crop.keys()))
            assert 0.0 <= crop["confidence"] <= 1.0

    def test_run_fertilizer_has_model_label(self, client):
        d = client.post("/api/analysis/run").get_json()
        assert "model_label" in d["fertilizer"]

    def test_run_irrigation_has_urgency(self, client):
        d = client.post("/api/analysis/run").get_json()
        assert "urgency" in d["irrigation"]
        assert d["irrigation"]["urgency"] in (
            "critical", "high", "medium", "low", "none", "unknown"
        )

    def test_run_with_bad_reading_id_returns_404(self, client):
        r = client.post("/api/analysis/run", json={"reading_id": 999999})
        assert r.status_code == 404

    def test_run_with_invalid_reading_id_type_returns_422(self, client):
        r = client.post("/api/analysis/run", json={"reading_id": "abc"})
        assert r.status_code == 422

    def test_run_with_manual_sensor_data(self, client):
        payload = {
            "sensor_data": {
                "nitrogen": 75.0,
                "phosphorus": 45.0,
                "potassium": 190.0,
                "ph": 6.8,
                "moisture": 55.0,
                "soil_temperature": 25.0,
                "air_temperature": 28.0,
                "air_humidity": 65.0,
                "source": "manual",
            },
            "soil_type": "Loamy",
            "notes": "Software test field #1",
        }
        r = client.post("/api/analysis/run", json=payload)
        assert r.status_code == 200
        d = r.get_json()
        assert d["sensor_reading"]["source"] == "manual"
        assert d["sensor_reading"]["nitrogen"] == 75.0
        assert d["sensor_reading"]["ph"] == 6.8
        assert d["soil"]["type"] == "Loamy"
        assert len(d["crops"]) == 3
        assert "fertilizer" in d["fertilizer"]

    def test_run_with_invalid_sensor_data_field(self, client):
        payload = {
            "sensor_data": {
                "nitrogen": "not_a_number",
            }
        }
        r = client.post("/api/analysis/run", json=payload)
        assert r.status_code == 422

    def test_run_with_image_path_linkage(self, client):
        payload = {
            "sensor_data": {"ph": 6.5, "moisture": 45.0},
            "soil_type": "Clayey",
            "image_path": "uploads/test_clay_sample.jpg",
        }
        r = client.post("/api/analysis/run", json=payload)
        assert r.status_code == 200
        d = r.get_json()
        assert d["soil"]["type"] == "Clayey"
        analysis_id = d["analysis_id"]
        res = client.get(f"/api/analysis/{analysis_id}").get_json()
        assert res["soil_image_path"] == "uploads/test_clay_sample.jpg"

    def test_run_with_manual_rainfall_and_moisture_preserved(self, client):
        """Rainfall and moisture must remain separate values and not conflated."""
        payload = {
            "sensor_data": {
                "rainfall": 125.0,
                "moisture": 42.0,
                "ph": 6.7,
                "nitrogen": 60.0,
                "phosphorus": 35.0,
                "potassium": 150.0,
                "source": "manual",
            },
            "soil_type": "Loamy",
        }
        r = client.post("/api/analysis/run", json=payload)
        assert r.status_code == 200
        d = r.get_json()
        assert d["sensor_reading"]["source"] == "manual"
        assert d["sensor_reading"]["rainfall"] == 125.0
        assert d["sensor_reading"]["moisture"] == 42.0
        assert d["soil"]["type"] == "Loamy"

    def test_run_with_invalid_rainfall_returns_422(self, client):
        payload = {
            "sensor_data": {
                "rainfall": "excessive_rain",
            }
        }
        r = client.post("/api/analysis/run", json=payload)
        assert r.status_code == 422

    def test_run_alluvial_soil_without_texture_withheld(self, client):
        payload = {
            "sensor_data": {"ph": 6.8, "moisture": 50.0, "nitrogen": 45.0},
            "soil_type": "Alluvial",
        }
        r = client.post("/api/analysis/run", json=payload)
        assert r.status_code == 200
        d = r.get_json()
        assert d["soil"]["type"] == "Alluvial"
        assert d["fertilizer"]["fertilizer"] == "Reliable recommendation unavailable"
        assert d["fertilizer"]["status"] == "unsupported"

    def test_run_alluvial_soil_with_confirmed_texture(self, client):
        payload = {
            "sensor_data": {"ph": 6.8, "moisture": 50.0, "nitrogen": 45.0},
            "soil_type": "Alluvial",
            "confirmed_soil_texture": "Clayey",
        }
        r = client.post("/api/analysis/run", json=payload)
        assert r.status_code == 200
        d = r.get_json()
        assert d["soil"]["type"] == "Alluvial"
        assert d["soil"]["confirmed_soil_texture"] == "Clayey"

    def test_run_with_missing_image_file_handled_gracefully(self, client):
        payload = {
            "sensor_data": {"ph": 6.8, "moisture": 50.0},
            "image_path": "uploads/nonexistent_sample_img.jpg",
        }
        r = client.post("/api/analysis/run", json=payload)
        assert r.status_code == 200
        d = r.get_json()
        assert d["soil"]["cnn_status"] == "not_found"
        assert d["soil"]["type"] is not None

    def test_history_returns_200(self, client):
        client.post("/api/analysis/run")
        r = client.get("/api/analysis/history")
        assert r.status_code == 200

    def test_history_pagination_structure(self, client):
        d = client.get("/api/analysis/history").get_json()
        assert {"items", "total", "page", "per_page", "pages"}.issubset(set(d.keys()))

    def test_get_analysis_by_id(self, client):
        d = client.post("/api/analysis/run").get_json()
        analysis_id = d["analysis_id"]
        r = client.get(f"/api/analysis/{analysis_id}")
        assert r.status_code == 200
        assert r.get_json()["id"] == analysis_id

    def test_get_analysis_not_found(self, client):
        r = client.get("/api/analysis/999999")
        assert r.status_code == 404


# ── Predictions ───────────────────────────────────────────────────────────────

class TestPredictionEndpoints:

    def test_latest_after_analysis_returns_200(self, client):
        client.post("/api/analysis/run")
        r = client.get("/api/predictions/latest")
        assert r.status_code == 200

    def test_latest_no_data_returns_404(self, client):
        # Fresh test client — no analysis run yet
        from app import create_app
        fresh_app = create_app("testing")
        with fresh_app.test_client() as fresh_client:
            with fresh_app.app_context():
                from app.extensions import db
                db.create_all()
                r = fresh_client.get("/api/predictions/latest")
                assert r.status_code == 404

    def test_latest_has_prediction_types(self, client):
        client.post("/api/analysis/run")
        d = client.get("/api/predictions/latest").get_json()
        preds = d.get("predictions", {})
        assert "crop"       in preds
        assert "fertilizer" in preds
        assert "irrigation" in preds

    def test_history_returns_200(self, client):
        client.post("/api/analysis/run")
        r = client.get("/api/predictions/history")
        assert r.status_code == 200

    def test_history_filter_by_type(self, client):
        client.post("/api/analysis/run")
        d = client.get("/api/predictions/history?prediction_type=crop").get_json()
        for item in d["items"]:
            assert item["prediction_type"] == "crop"

    def test_get_prediction_by_id(self, client):
        analysis = client.post("/api/analysis/run").get_json()
        pred_id = analysis["prediction_ids"]["crop"]
        r = client.get(f"/api/predictions/{pred_id}")
        assert r.status_code == 200
        assert r.get_json()["id"] == pred_id

    def test_get_prediction_not_found(self, client):
        r = client.get("/api/predictions/999999")
        assert r.status_code == 404


# ── Images ────────────────────────────────────────────────────────────────────

class TestImageEndpoints:

    def test_upload_valid_png_returns_200(self, client):
        r = client.post(
            "/api/images/upload",
            data={"image": (io.BytesIO(make_png()), "soil.png", "image/png")},
            content_type="multipart/form-data",
        )
        assert r.status_code == 200

    def test_upload_returns_filename(self, client):
        r = client.post(
            "/api/images/upload",
            data={"image": (io.BytesIO(make_png()), "soil.png", "image/png")},
            content_type="multipart/form-data",
        )
        d = r.get_json()
        assert "filename" in d
        assert d["filename"].endswith(".png")

    def test_upload_cnn_status_returned(self, client):
        r = client.post(
            "/api/images/upload",
            data={"image": (io.BytesIO(make_png()), "soil.png", "image/png")},
            content_type="multipart/form-data",
        )
        d = r.get_json()
        assert "cnn_status" in d
        assert d["cnn_status"] in ("ok", "model_unavailable", "preprocessing_failed")

    def test_upload_bad_extension_returns_422(self, client):
        r = client.post(
            "/api/images/upload",
            data={"image": (io.BytesIO(b"MZPE"), "virus.exe", "application/octet-stream")},
            content_type="multipart/form-data",
        )
        assert r.status_code == 422

    def test_upload_fake_image_returns_422(self, client):
        r = client.post(
            "/api/images/upload",
            data={"image": (io.BytesIO(b"Not an image"), "fake.jpg", "image/jpeg")},
            content_type="multipart/form-data",
        )
        assert r.status_code == 422

    def test_upload_no_file_returns_400(self, client):
        r = client.post(
            "/api/images/upload",
            data={},
            content_type="multipart/form-data",
        )
        assert r.status_code == 400

    def test_serve_uploaded_image(self, client):
        upload_r = client.post(
            "/api/images/upload",
            data={"image": (io.BytesIO(make_png()), "soil.png", "image/png")},
            content_type="multipart/form-data",
        )
        filename = upload_r.get_json()["filename"]
        serve_r = client.get(f"/api/images/{filename}")
        assert serve_r.status_code == 200

    def test_serve_nonexistent_returns_404(self, client):
        r = client.get("/api/images/doesnotexist.jpg")
        assert r.status_code == 404

    def test_path_traversal_blocked(self, client):
        r = client.get("/api/images/../.env")
        assert r.status_code == 404

    def test_upload_with_run_analysis_true(self, client):
        r = client.post(
            "/api/images/upload",
            data={
                "image": (io.BytesIO(make_png()), "soil.png", "image/png"),
                "run_analysis": "true",
            },
            content_type="multipart/form-data",
        )
        assert r.status_code == 200
        d = r.get_json()
        assert "filename" in d
        assert "analysis" in d
        analysis = d["analysis"]
        assert "analysis_id" in analysis
        assert "crops" in analysis
        assert "fertilizer" in analysis
        assert "irrigation" in analysis
        assert "soil" in analysis
        assert analysis["soil"]["type"] is not None
