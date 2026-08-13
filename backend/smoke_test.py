"""
smoke_test.py — In-process API smoke test (no separate server needed).
Runs inside the Flask test client: no network port required.
Usage: python smoke_test.py  (from agrosmart/backend/)
"""
import json, sys, os
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("SENSOR_MODE", "simulator")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app

app = create_app("testing")

SEP = "-" * 64
PASS = "[PASS]"
FAIL = "[FAIL]"
errors = []

def check(label, cond, detail=""):
    if cond:
        print(f"  {PASS} {label}")
    else:
        print(f"  {FAIL} {label}  {detail}")
        errors.append(label)

with app.test_client() as c:

    # ── 1. Health ─────────────────────────────────────────────────────────────
    print(SEP)
    print("[1] GET /api/health")
    r = c.get("/api/health")
    d = json.loads(r.data)
    print(f"    HTTP {r.status_code}  |  {d}")
    check("status 200",        r.status_code == 200)
    check("status=ok",         d.get("status") == "ok")
    check("sensor_mode present", "sensor_mode" in d)

    # ── 2. Latest sensor reading ──────────────────────────────────────────────
    print(SEP)
    print("[2] GET /api/sensors/latest")
    r = c.get("/api/sensors/latest")
    d = json.loads(r.data)
    sd = d.get("data", d)   # some endpoints use {"data": ...} wrapper
    print(f"    HTTP {r.status_code}  |  moisture={sd.get('moisture')}  ph={sd.get('ph')}  N={sd.get('nitrogen')}")
    check("status 200",          r.status_code == 200)
    check("moisture present",    sd.get("moisture") is not None)
    check("ph present",          sd.get("ph") is not None)
    check("nitrogen present",    sd.get("nitrogen") is not None)

    # ── 3. Full analysis pipeline ─────────────────────────────────────────────
    print(SEP)
    print("[3] POST /api/analysis/run")
    r = c.post("/api/analysis/run", json={})
    d = json.loads(r.data)
    ad = d.get("data", d)
    soil = ad.get("soil", {})
    crops = ad.get("crops", [])
    fert = ad.get("fertilizer", {})
    irr  = ad.get("irrigation", {})
    print(f"    HTTP {r.status_code}  |  analysis_id={ad.get('analysis_id')}")
    print(f"    soil_type={soil.get('type')}  health={soil.get('health_status')}  score={soil.get('health_score')}")
    for cr in crops:
        print(f"    crop: {str(cr.get('crop')):22s}  conf={cr.get('confidence'):.3f}  rank={cr.get('rank')}")
    print(f"    fertilizer={fert.get('fertilizer')}  model_label={fert.get('model_label')}")
    print(f"    irrigation urgency={irr.get('urgency')}  action={irr.get('action')}")
    check("status 200",          r.status_code == 200)
    check("analysis_id present", ad.get("analysis_id") is not None)
    check("soil type present",   soil.get("type") is not None)
    check("crops returned",      len(crops) > 0)
    check("fertilizer returned", fert.get("fertilizer") not in (None, "N/A", "error"))
    check("irrigation returned", irr.get("urgency") is not None)

    # ── 4. Sensor history ─────────────────────────────────────────────────────
    print(SEP)
    print("[4] GET /api/sensors/history")
    r = c.get("/api/sensors/history?limit=3")
    check("status 200", r.status_code == 200)

    # ── 5. Analysis history ───────────────────────────────────────────────────
    print(SEP)
    print("[5] GET /api/analysis/history")
    r = c.get("/api/analysis/history?page=1&per_page=5")
    d = json.loads(r.data)
    ad2 = d.get("data", d)
    check("status 200",       r.status_code == 200)
    check("total >= 1",       ad2.get("total", 0) >= 1)

    # ── 6. Predictions latest ─────────────────────────────────────────────────
    print(SEP)
    print("[6] GET /api/predictions/latest")
    r = c.get("/api/predictions/latest")
    d = json.loads(r.data)
    # endpoint returns { analysis_id, timestamp, soil, predictions: {crop, fertilizer, irrigation} }
    preds = d.get("predictions", d.get("data", {}))
    check("status 200",           r.status_code == 200)
    check("crop prediction",      "crop" in preds)
    check("fertilizer prediction","fertilizer" in preds)
    check("irrigation prediction","irrigation" in preds)
    for ptype, pdata in preds.items():
        if isinstance(pdata, dict):
            print(f"    {ptype}: top={pdata.get('top_recommendation')}  model={pdata.get('model_version')}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(SEP)
    if not errors:
        print("ALL SMOKE TESTS PASSED  (6/6 endpoints OK)")
    else:
        print(f"FAILURES: {len(errors)}")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
