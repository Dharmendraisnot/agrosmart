"""
tests/test_soil_cnn_warmup.py — Unit and concurrency tests for CNN warmup mechanism.

Tests:
  - Idempotent behavior when model is already loaded.
  - Thread-safety under concurrent warmup calls.
  - Request arriving during warmup waits safely for completion without restarting initialization.
  - Warmup failure (e.g. missing model file) is handled gracefully and sets model_unavailable.
  - Warmup timeout returns model_unavailable with a timeout message.
  - Flask reloader parent process skips background warmup.
  - reload_model cleanly resets all state and synchronization primitives.
"""
import os
import threading
import time
import numpy as np
import pytest

from app.ml import soil_cnn


@pytest.fixture(autouse=True)
def clean_cnn_state():
    """Ensure CNN state is cleaned up after each test."""
    yield
    soil_cnn.reload_model()


class TestSoilCNNWarmup:

    def test_warmup_model_already_ready_is_idempotent(self, app):
        """When model is already ready, warmup_model returns True immediately without starting threads."""
        class DummyModel:
            def predict(self, x, verbose=0):
                return np.array([[0.25, 0.25, 0.25, 0.25]])

        soil_cnn._model = DummyModel()
        soil_cnn._classes = ["Alluvial", "Black", "Clay", "Red"]

        assert soil_cnn.is_model_ready() is True
        result = soil_cnn.warmup_model(app.config, async_mode=False)
        assert result is True
        assert soil_cnn.is_warming_up() is False

    def test_concurrent_warmup_calls_no_duplicates(self, app):
        """Multiple concurrent calls to warmup_model must not trigger race conditions or duplicate loads."""
        class MockModel:
            def predict(self, x, verbose=0):
                return np.array([[0.1, 0.2, 0.3, 0.4]])

        load_count = 0
        load_lock = threading.Lock()

        def fake_load(config):
            nonlocal load_count
            time.sleep(0.05)
            with load_lock:
                load_count += 1
            soil_cnn._model = MockModel()
            soil_cnn._classes = ["Alluvial", "Black", "Clay", "Red"]
            return True

        orig_load = soil_cnn._load
        soil_cnn._load = fake_load
        try:
            results = []
            threads = []

            def worker():
                res = soil_cnn.warmup_model(app.config, async_mode=False)
                results.append(res)

            for _ in range(5):
                t = threading.Thread(target=worker)
                threads.append(t)
                t.start()

            for t in threads:
                t.join(timeout=5.0)

            assert len(results) == 5
            assert all(r is True for r in results)
            assert load_count == 1  # Loaded strictly once
        finally:
            soil_cnn._load = orig_load

    def test_inference_during_warmup_waits_for_ready_event(self, app):
        """Inference request arriving while warmup is in progress must wait safely for readiness."""
        class MockModel:
            def predict(self, x, verbose=0):
                return np.array([[0.1, 0.2, 0.3, 0.4]])

        soil_cnn._is_warming_up = True
        soil_cnn._ready_event.clear()

        def background_finish_warmup():
            time.sleep(0.1)
            soil_cnn._model = MockModel()
            soil_cnn._classes = ["Alluvial", "Black", "Clay", "Red"]
            soil_cnn._is_warming_up = False
            soil_cnn._ready_event.set()

        t = threading.Thread(target=background_finish_warmup)
        t.start()

        img = np.zeros((224, 224, 3), dtype=np.float32)
        res = soil_cnn.predict_soil_type(img, app.config, wait_timeout=2.0)
        t.join(timeout=2.0)

        assert res["status"] == "ok"
        assert res["soil_type"] == "Red"
        assert res["confidence"] == 0.4

    def test_warmup_failure_handled_gracefully(self, monkeypatch):
        """If warmup fails (e.g. invalid path), error is captured and predict returns model_unavailable."""
        monkeypatch.setattr(soil_cnn, "_check_tf", lambda: True)
        bad_config = {"SOIL_CNN_MODEL_PATH": "nonexistent_model_file.h5"}
        success = soil_cnn.warmup_model(bad_config, async_mode=False)
        assert success is False
        assert soil_cnn.is_model_ready() is False

        img = np.zeros((224, 224, 3), dtype=np.float32)
        res = soil_cnn.predict_soil_type(img, bad_config)
        assert res["status"] == "model_unavailable"
        assert res["soil_type"] is None

    def test_warmup_tf_unavailable_handled_gracefully(self, monkeypatch):
        """If TensorFlow is not available, warmup fails gracefully with informative error."""
        monkeypatch.setattr(soil_cnn, "_check_tf", lambda: False)
        success = soil_cnn.warmup_model({}, async_mode=False)
        assert success is False
        assert soil_cnn.is_model_ready() is False

        img = np.zeros((224, 224, 3), dtype=np.float32)
        res = soil_cnn.predict_soil_type(img, {})
        assert res["status"] == "model_unavailable"
        assert "TensorFlow" in res.get("error", "")

    def test_inference_timeout_while_warming_up(self, app):
        """If warmup does not finish within wait_timeout, predict returns model_unavailable with timeout error."""
        soil_cnn._is_warming_up = True
        soil_cnn._ready_event.clear()

        try:
            img = np.zeros((224, 224, 3), dtype=np.float32)
            res = soil_cnn.predict_soil_type(img, app.config, wait_timeout=0.05)
            assert res["status"] == "model_unavailable"
            assert "Warmup timed out" in res.get("error", "")
        finally:
            soil_cnn._is_warming_up = False
            soil_cnn._ready_event.set()

    def test_reloader_parent_process_skips_warmup(self, monkeypatch):
        """Werkzeug reloader parent process (where WERKZEUG_RUN_MAIN is unset) must skip warmup."""
        warmup_called = False

        def mock_warmup(*args, **kwargs):
            nonlocal warmup_called
            warmup_called = True

        monkeypatch.setattr(soil_cnn, "warmup_model", mock_warmup)

        # Case 1: In testing, warmup should not be called
        from app import create_app
        create_app("testing")
        assert warmup_called is False

        # Case 2: In development with debug=True, if WERKZEUG_RUN_MAIN is unset, skip warmup
        monkeypatch.delenv("WERKZEUG_RUN_MAIN", raising=False)
        create_app("development")
        assert warmup_called is False

        # Case 3: In development with debug=True, if WERKZEUG_RUN_MAIN is "true", run warmup
        monkeypatch.setenv("WERKZEUG_RUN_MAIN", "true")
        create_app("development")
        assert warmup_called is True

    def test_reload_model_resets_all_state(self):
        """reload_model resets model, classes, warmup state, and event."""
        soil_cnn._model = "fake_model"
        soil_cnn._classes = ["Alluvial"]
        soil_cnn._is_warming_up = True
        soil_cnn._ready_event.set()

        soil_cnn.reload_model()

        assert soil_cnn.is_model_ready() is False
        assert soil_cnn.is_warming_up() is False
        assert soil_cnn._ready_event.is_set() is False
