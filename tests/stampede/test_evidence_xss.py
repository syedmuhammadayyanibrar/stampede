import re
from pathlib import Path
from fastapi.testclient import TestClient
from server import app
from stampede.api.security import rate_limiter

client = TestClient(app)

def test_evidence_endpoint_returns_raw_payload():
    rate_limiter.reset()
    resp_create = client.post("/api/v1/sessions")
    session_id = resp_create.json()["session_id"]

    script_payload = "<script>alert('xss_vulnerability')</script><img src=x onerror=alert(1)>"
    custom_workload = [
        {
            "id": "xss_test_prompt",
            "text": script_payload,
            "checks": [{"type": "exact_match", "expected": script_payload}]
        }
    ]
    client.post(f"/api/v1/sessions/{session_id}/inputs", json={"workload": custom_workload})
    client.post(f"/api/v1/sessions/{session_id}/estimate")
    resp_run = client.post(f"/api/v1/sessions/{session_id}/run", json={"confirm_estimate": True})
    assert resp_run.status_code == 200

    resp_ev = client.get(f"/api/v1/sessions/{session_id}/evidence/0")
    assert resp_ev.status_code == 200
    ev_data = resp_ev.json()
    assert ev_data["prompt_index"] == 0
    assert script_payload in ev_data["prompt_text"]

def test_web_ui_evidence_drawer_uses_text_content_never_inner_html():
    app_js_path = Path("web/app.js")
    assert app_js_path.exists()
    content = app_js_path.read_text(encoding="utf-8", errors="ignore")

    drawer_matches = re.findall(r"(?:drawer|evidence|model_output)[^;{}\n]*innerHTML", content, re.IGNORECASE)
    assert len(drawer_matches) == 0, f"Found innerHTML in evidence drawer: {drawer_matches}"

    assert "textContent" in content

def test_literal_text_escaping_simulation():
    payload = "<script>alert('pwn')</script>"
    escaped_in_text_node = payload.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    assert "<script>" not in escaped_in_text_node
    assert "&lt;script&gt;" in escaped_in_text_node
