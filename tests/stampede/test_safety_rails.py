import os
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_sentinel_byok_key_never_persisted_or_leaked():
    sentinel = "sk-sentinel-secret-rail-998877"

    resp_create = client.post("/api/v1/sessions", json={"byok_key": sentinel})
    assert resp_create.status_code == 200
    data_create = resp_create.json()
    assert sentinel not in str(data_create)
    session_id = data_create["session_id"]

    resp_get = client.get(f"/api/v1/sessions/{session_id}")
    assert resp_get.status_code == 200
    assert sentinel not in str(resp_get.json())

    resp_est = client.post(f"/api/v1/sessions/{session_id}/estimate")
    assert resp_est.status_code == 200
    assert sentinel not in str(resp_est.json())

    headers = {"X-Provider-Key": sentinel}
    resp_run = client.post(f"/api/v1/sessions/{session_id}/run", json={"confirm_estimate": True}, headers=headers)
    assert resp_run.status_code == 200
    assert sentinel not in str(resp_run.json())

    db_path = Path("data/stampede_sessions_meta.db")
    if db_path.exists():
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM session_meta WHERE session_id = ?", (session_id,))
            rows = cursor.fetchall()
            for row in rows:
                for col in row:
                    assert sentinel not in str(col)

    logs_dir = Path("logs")
    if logs_dir.exists():
        for log_file in logs_dir.glob("*.log"):
            content = log_file.read_text(encoding="utf-8", errors="ignore")
            assert sentinel not in content

    resp_del = client.delete(f"/api/v1/sessions/{session_id}")
    assert resp_del.status_code == 200
    assert sentinel not in str(resp_del.json())

def test_kill_switch_env_behavior():
    resp_create = client.post("/api/v1/sessions")
    session_id = resp_create.json()["session_id"]
    client.post(f"/api/v1/sessions/{session_id}/estimate")

    os.environ["STAMPEDE_KILL"] = "1"
    try:
        resp_run = client.post(f"/api/v1/sessions/{session_id}/run", json={"confirm_estimate": True})
        assert resp_run.status_code == 503

        resp_get = client.get(f"/api/v1/sessions/{session_id}")
        assert resp_get.status_code == 200

        resp_del = client.delete(f"/api/v1/sessions/{session_id}")
        assert resp_del.status_code == 200
    finally:
        os.environ.pop("STAMPEDE_KILL", None)

def test_kill_switch_file_behavior():
    resp_create = client.post("/api/v1/sessions")
    session_id = resp_create.json()["session_id"]
    client.post(f"/api/v1/sessions/{session_id}/estimate")

    kill_file = Path("data/KILL")
    kill_file.parent.mkdir(parents=True, exist_ok=True)
    kill_file.write_text("1", encoding="utf-8")
    try:
        resp_run = client.post(f"/api/v1/sessions/{session_id}/run", json={"confirm_estimate": True})
        assert resp_run.status_code == 503

        resp_get = client.get(f"/api/v1/sessions/{session_id}")
        assert resp_get.status_code == 200

        resp_del = client.delete(f"/api/v1/sessions/{session_id}")
        assert resp_del.status_code == 200
    finally:
        if kill_file.exists():
            kill_file.unlink()

from stampede.api.security import rate_limiter

def test_run_requires_prior_estimate_and_confirmation():
    rate_limiter.reset()
    resp_create = client.post("/api/v1/sessions")
    session_id = resp_create.json()["session_id"]

    resp_no_est = client.post(f"/api/v1/sessions/{session_id}/run", json={"confirm_estimate": True})
    assert resp_no_est.status_code == 400

    resp_est = client.post(f"/api/v1/sessions/{session_id}/estimate")
    assert resp_est.status_code == 200
    est_data = resp_est.json()

    if est_data["total_cost_usd_hi"] > 0.50:
        resp_no_confirm = client.post(f"/api/v1/sessions/{session_id}/run", json={"confirm_estimate": False})
        assert resp_no_confirm.status_code == 400

    resp_ok = client.post(f"/api/v1/sessions/{session_id}/run", json={"confirm_estimate": True})
    assert resp_ok.status_code == 200
