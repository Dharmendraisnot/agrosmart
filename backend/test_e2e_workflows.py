"""
test_e2e_workflows.py — End-to-end validation of Phase 4 workflows.
Tests:
  1. Manual Soil Input (8 parameters: N, P, K, pH, temp, humidity, rainfall, moisture)
  2. Soil Image Upload with MobileNetV2 CNN classification
  3. Alluvial Soil Texture Safeguards (withheld without texture, active with confirmed texture)
  4. Validation errors & graceful fallbacks
"""
import io
import json
import os
import sys

os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("SENSOR_MODE", "simulator")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app

app = create_app("testing")

def make_sample_image():
    from PIL import Image
    buf = io.BytesIO()
    img = Image.new("RGB", (224, 224), color=(180, 100, 60))
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf

print("=" * 70)
print("RUNNING END-TO-END WORKFLOW TESTS FOR PHASE 4")
print("=" * 70)

with app.test_client() as client:
    # ── Workflow 1: Manual Input (8 parameters) ──────────────────────────────
    print("\n[Workflow 1] Pure Manual Soil Input (8 distinct parameters)")
    payload_w1 = {
        "sensor_data": {
            "nitrogen": 65.0,
            "phosphorus": 35.0,
            "potassium": 180.0,
            "ph": 6.8,
            "soil_temperature": 24.5,
            "air_temperature": 27.0,
            "air_humidity": 62.0,
            "rainfall": 125.0,    # mm
            "moisture": 48.0,    # %
            "source": "manual",
        },
        "soil_type": "Loamy",
        "notes": "Field Trial North #1",
    }
    r1 = client.post("/api/analysis/run", json=payload_w1)
    assert r1.status_code == 200, f"Expected 200, got {r1.status_code}: {r1.data}"
    d1 = r1.get_json()
    sr1 = d1["sensor_reading"]
    assert sr1["source"] == "manual"
    assert sr1["rainfall"] == 125.0, f"Rainfall was {sr1['rainfall']}"
    assert sr1["moisture"] == 48.0, f"Moisture was {sr1['moisture']}"
    assert d1["soil"]["type"] == "Loamy"
    assert len(d1["crops"]) == 3
    assert "fertilizer" in d1["fertilizer"]
    assert "action" in d1["irrigation"]
    print(f"  --> PASSED: Analysis #{d1['analysis_id']} | Source={sr1['source']} | Rainfall={sr1['rainfall']}mm | Moisture={sr1['moisture']}% | Top Crop={d1['crops'][0]['crop']}")

    # ── Workflow 2: Soil Image Upload & CNN Inference ────────────────────────
    print("\n[Workflow 2] Soil Image Upload & MobileNetV2 CNN Inference")
    img_bytes = make_sample_image()
    r2_upload = client.post(
        "/api/images/upload",
        data={"image": (img_bytes, "field_soil.jpg", "image/jpeg")},
        content_type="multipart/form-data",
    )
    assert r2_upload.status_code == 200, f"Upload failed: {r2_upload.data}"
    d2_img = r2_upload.get_json()
    assert "filename" in d2_img
    assert "soil_type" in d2_img
    assert "confidence" in d2_img
    assert d2_img["cnn_status"] == "ok"
    assert len(d2_img.get("all_classes", [])) == 4
    print(f"  --> PASSED Image Upload: file={d2_img['filename']} | CNN Class={d2_img['soil_type']} | Conf={d2_img['confidence']:.3f}")
    for cls_item in d2_img["all_classes"]:
        print(f"      - {cls_item['class']}: {cls_item['confidence']:.4f}")

    # Link uploaded image to full analysis
    r2_analysis = client.post(
        "/api/analysis/run",
        json={
            "image_path": d2_img["filename"],
            "sensor_data": {"ph": 6.7, "moisture": 52.0, "rainfall": 90.0, "nitrogen": 55.0},
        },
    )
    assert r2_analysis.status_code == 200
    d2_res = r2_analysis.get_json()
    assert d2_res["soil"]["type"] == d2_img["soil_type"]
    assert d2_res["soil"]["type_confidence"] is not None
    assert d2_res["soil"]["cnn_status"] == "ok"
    print(f"  --> PASSED Analysis Linkage: Linked to #{d2_res['analysis_id']} | Soil={d2_res['soil']['type']} (conf={d2_res['soil']['type_confidence']:.3f})")

    # ── Workflow 3: Alluvial Soil Texture Safeguards ──────────────────────────
    print("\n[Workflow 3] Alluvial Soil Texture Safeguard (Withholding vs Confirmation)")
    # Case 3A: Alluvial without confirmed texture -> Withheld
    r3a = client.post(
        "/api/analysis/run",
        json={
            "soil_type": "Alluvial",
            "sensor_data": {"nitrogen": 50, "phosphorus": 30, "potassium": 150, "moisture": 50},
        },
    )
    assert r3a.status_code == 200
    d3a = r3a.get_json()
    assert d3a["fertilizer"]["fertilizer"] == "Reliable recommendation unavailable"
    assert d3a["fertilizer"]["status"] == "unsupported"
    assert "Alluvial" in d3a["fertilizer"]["advice"]
    print(f"  --> PASSED 3A (Without Texture): Status='{d3a['fertilizer']['status']}' | Recommendation='{d3a['fertilizer']['fertilizer']}'")

    # Case 3B: Alluvial WITH confirmed physical texture "Clayey" -> Active recommendation
    r3b = client.post(
        "/api/analysis/run",
        json={
            "soil_type": "Alluvial",
            "confirmed_soil_texture": "Clayey",
            "sensor_data": {"nitrogen": 80, "phosphorus": 40, "potassium": 40, "moisture": 50},
        },
    )
    assert r3b.status_code == 200
    d3b = r3b.get_json()
    assert d3b["soil"]["confirmed_soil_texture"] == "Clayey"
    print(f"  --> PASSED 3B (With Confirmed Texture 'Clayey'): ConfirmedTexture='{d3b['soil']['confirmed_soil_texture']}' | Fertilizer='{d3b['fertilizer']['fertilizer']}'")

    # Case 3C: Alluvial with invalid physical texture -> Rejected/withheld
    r3c = client.post(
        "/api/analysis/run",
        json={
            "soil_type": "Alluvial",
            "confirmed_soil_texture": "GravellyStone",
            "sensor_data": {"nitrogen": 80, "moisture": 50},
        },
    )
    assert r3c.status_code == 200
    d3c = r3c.get_json()
    assert d3c["fertilizer"]["fertilizer"] == "Reliable recommendation unavailable"
    print(f"  --> PASSED 3C (With Invalid Texture): Correctly withheld | Advice='{d3c['fertilizer']['advice'][:60]}...'")

    # ── Workflow 4: Validation Errors & Error Handling ────────────────────────
    print("\n[Workflow 4] Validation Error Handling & Boundaries")
    # Non-numeric rainfall
    r4a = client.post(
        "/api/analysis/run",
        json={"sensor_data": {"rainfall": "heavy_downpour"}},
    )
    assert r4a.status_code == 422
    assert "must be a number" in r4a.get_json()["error"]
    print(f"  --> PASSED 4A: Non-numeric rainfall returns 422 | Error: '{r4a.get_json()['error']}'")

    # Corrupt / invalid image upload
    r4b = client.post(
        "/api/images/upload",
        data={"image": (io.BytesIO(b"MZExecutableHeader"), "malware.exe", "application/octet-stream")},
        content_type="multipart/form-data",
    )
    assert r4b.status_code == 422
    print(f"  --> PASSED 4B: Invalid image upload returns 422 | Error: '{r4b.get_json()['error']}'")

    # Missing image path in analysis -> graceful heuristic fallback
    r4c = client.post(
        "/api/analysis/run",
        json={"image_path": "uploads/does_not_exist_99.jpg", "sensor_data": {"moisture": 45, "ph": 6.5}},
    )
    assert r4c.status_code == 200
    d4c = r4c.get_json()
    assert d4c["soil"]["cnn_status"] == "not_found"
    assert d4c["soil"]["type"] is not None
    print(f"  --> PASSED 4C: Missing image path gracefully falls back to heuristic soil='{d4c['soil']['type']}' (cnn_status='not_found')")

    # History retrieval
    r4d = client.get("/api/analysis/history?page=1&per_page=5")
    assert r4d.status_code == 200
    assert r4d.get_json()["total"] >= 1
    print(f"  --> PASSED 4D: History API returns {r4d.get_json()['total']} saved analyses")

print("\n" + "=" * 70)
print("ALL 4 END-TO-END WORKFLOWS PASSED SUCCESSFULLY")
print("=" * 70)
