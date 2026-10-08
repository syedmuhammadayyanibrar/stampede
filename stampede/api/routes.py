import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import StreamingResponse, JSONResponse
from stampede.sessions import session_store
from stampede.events import EventLog
from stampede.orchestrator import PipelineOrchestrator
from stampede.costs import estimate_run_cost, global_cost_ledger
from stampede.settings import settings
from stampede.sample import SAMPLE_USAGE_DATA, SAMPLE_QUOTES, load_sample_prompts, get_sample_replay_notice
from stampede.stages.ingest import ingest_usage_csv, generate_synthetic_usage_series
from stampede.stages.constraints_parse import parse_constraints
from stampede.stages.quotes_parse import parse_quotes_text
from stampede.stages.valuation_live import compute_reservation_prices_table
from stampede.stages.rfq import build_structured_rfq, render_rfq_email_template
from stampede.whatif import execute_whatif_recompute
from stampede.stages.seller_view import compute_seller_uplift
from stampede.explain import generate_shapley_explanation
from stampede.api.security import rate_limiter, validate_workload_input, validate_quote_text_length, validate_usage_csv_size

router = APIRouter()
session_event_logs: Dict[str, EventLog] = {}

@router.post("/sessions")
def create_session(request: Request, body: Optional[Dict[str, Any]] = None):
    ip = request.client.host if request.client else "127.0.0.1"
    if not rate_limiter.check_read(ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    byok = body.get("byok_key") if body else None
    sess = session_store.create_session(byok_key=byok)
    session_event_logs[sess.session_id] = EventLog()
    return {"session_id": sess.session_id, "created_at": sess.created_at}

@router.get("/sessions/{session_id}")
def get_session(session_id: str, request: Request):
    ip = request.client.host if request.client else "127.0.0.1"
    if not rate_limiter.check_read(ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return {
        "session_id": sess.session_id,
        "created_at": sess.created_at,
        "last_active_at": sess.last_active_at,
        "notices": [n.model_dump() for n in sess.notices],
        "total_spend_usd": sess.total_spend_usd,
        "has_run": "latest" in sess.run_records
    }

@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    session_store.delete_session(session_id)
    session_event_logs.pop(session_id, None)
    return {"status": "deleted", "session_id": session_id}

@router.post("/sessions/{session_id}/inputs")
def update_inputs(session_id: str, payload: Dict[str, Any]):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    for k in ["usage", "workload", "constraints", "quotes"]:
        if k in payload:
            sess.inputs[k] = payload[k]
    return {"status": "inputs_updated", "session_id": session_id}

@router.put("/sessions/{session_id}/usage")
def update_usage_endpoint(session_id: str, body: Dict[str, Any]):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    if "csv_content" in body:
        csv_text = str(body["csv_content"])
        validate_usage_csv_size(len(csv_text))
        report = ingest_usage_csv(csv_text)
        if not report.success:
            raise HTTPException(status_code=400, detail=report.error or "Usage CSV parsing failed invariants")
        sess.inputs["usage"] = report.daily_series.values
        return report.model_dump()
    elif "monthly_tokens" in body:
        m_tokens = float(body.get("monthly_tokens", 30000000.0))
        report = generate_synthetic_usage_series(days=90, base_daily_tokens=m_tokens / 30.0)
        sess.inputs["usage"] = report.daily_series.values
        return report.model_dump()
    else:
        raise HTTPException(status_code=400, detail="Invalid usage payload")

@router.put("/sessions/{session_id}/workload")
def update_workload_endpoint(session_id: str, body: Dict[str, Any]):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    prompts = body.get("prompts", [])
    validate_workload_input(prompts)
    sess.inputs["workload"] = prompts
    return {"status": "workload_updated", "count": len(prompts)}

@router.put("/sessions/{session_id}/quotes")
def update_quotes_endpoint(session_id: str, body: Dict[str, Any]):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    quotes = body.get("quotes", [])
    sess.inputs["quotes"] = quotes
    return {"status": "quotes_updated", "count": len(quotes)}

@router.post("/sessions/{session_id}/load-sample")
def load_sample_endpoint(session_id: str):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    sess.inputs["usage"] = SAMPLE_USAGE_DATA
    sess.inputs["workload"] = [p.model_dump() for p in load_sample_prompts()]
    sess.inputs["quotes"] = [q.model_dump() for q in SAMPLE_QUOTES]
    sess.notices.append(get_sample_replay_notice())
    return {
        "status": "sample_loaded",
        "session_id": session_id,
        "prompts_count": len(sess.inputs["workload"]),
        "quotes_count": len(sess.inputs["quotes"])
    }

@router.post("/sessions/{session_id}/estimate")
def get_session_estimate(session_id: str, request: Request):
    ip = request.client.host if request.client else "127.0.0.1"
    if not rate_limiter.check_read(ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    stages = ["ingest", "parity", "narrative", "forecast", "quotes", "valuation", "plan", "exit", "seller"]
    num_prompts = len(sess.inputs.get("workload") or []) or 24
    num_candidates = len(sess.inputs.get("quotes") or []) or 2
    est = estimate_run_cost(
        stages=stages,
        num_prompts=num_prompts,
        num_candidates=num_candidates,
        session_spend_usd=sess.total_spend_usd,
        is_byok=bool(sess.byok_key),
        is_judged=True
    )
    sess.session_cache["latest_estimate"] = est
    return est.model_dump()

@router.post("/sessions/{session_id}/run")
async def trigger_run(session_id: str, request: Request, x_provider_key: Optional[str] = Header(None, alias="X-Provider-Key")):
    if os.environ.get("STAMPEDE_KILL") == "1" or Path("data/KILL").exists():
        raise HTTPException(status_code=503, detail="Kill switch active")
    ip = request.client.host if request.client else "127.0.0.1"
    if not rate_limiter.check_run(ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    est = sess.session_cache.get("latest_estimate")
    if not est:
        raise HTTPException(status_code=400, detail="Estimate must be requested via POST /sessions/{id}/estimate before run")
    if x_provider_key:
        sess.byok_key = x_provider_key
    rem_session = max(0.0, settings.session_cap_usd - sess.total_spend_usd)
    if est.total_cost_usd_hi > rem_session and not sess.byok_key:
        raise HTTPException(status_code=400, detail="High estimate exceeds remaining session cap")
    if est.total_cost_usd_hi > 0.50:
        if not body or not body.get("confirm_estimate", False):
            raise HTTPException(status_code=400, detail="Estimate confirmation required above 0.50 USD")
    if not sess.byok_key:
        rem_daily = global_cost_ledger.get_remaining_daily_budget()
        if est.total_cost_usd_hi > rem_daily:
            raise HTTPException(status_code=400, detail="High estimate exceeds remaining daily cap")
    ev_log = session_event_logs.get(session_id)
    if not ev_log:
        ev_log = EventLog()
        session_event_logs[session_id] = ev_log
    orchestrator = PipelineOrchestrator(session=sess, event_log=ev_log)
    run_res = orchestrator.run_full_pipeline()
    return {"status": "COMPLETED", "run_id": f"run_{session_id}"}

@router.get("/sessions/{session_id}/events")
def get_events(session_id: str, last_event_id: Optional[str] = Header(None, alias="Last-Event-ID")):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    ev_log = session_event_logs.get(session_id)
    if not ev_log:
        raise HTTPException(status_code=404, detail="No event stream for session")

    lid = int(last_event_id) if last_event_id and last_event_id.isdigit() else None
    events = ev_log.get_events_since(lid)

    def event_generator():
        for e in events:
            yield e.to_sse_format()

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/sessions/{session_id}/results")
def get_results(session_id: str):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    run_state = sess.run_records.get("latest")
    if not run_state:
        raise HTTPException(status_code=404, detail="No run results available")
    return {k: v for k, v in run_state.items() if k not in ("random_draws", "history_tokens")}

@router.get("/sessions/{session_id}/evidence/{prompt_idx}")
def get_evidence_item(session_id: str, prompt_idx: int):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    run_state = sess.run_records.get("latest") or sess.session_cache
    evidence_list = run_state.get("evidence", [])
    for ev in evidence_list:
        if ev.get("prompt_index") == prompt_idx:
            return ev
    raise HTTPException(status_code=404, detail=f"Evidence for prompt index {prompt_idx} not found")

@router.get("/sessions/{session_id}/evidence")
def list_session_evidence(session_id: str):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    run_state = sess.run_records.get("latest") or sess.session_cache
    evidence_list = run_state.get("evidence", [])
    return {"evidence": evidence_list, "count": len(evidence_list)}

@router.get("/sessions/{session_id}/reservation-prices")
def get_reservation_prices_endpoint(session_id: str, rho: float = 0.5):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    table = compute_reservation_prices_table(rho=rho, random_draws=sess.draws)
    return [r.model_dump() for r in table]

@router.get("/sessions/{session_id}/waterfall")
def get_waterfall_endpoint(session_id: str):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    run_state = sess.run_records.get("latest") or sess.session_cache
    if "waterfall" in run_state:
        return run_state["waterfall"]
    from stampede.stages.waterfall import compute_net_saving_waterfall
    res = compute_net_saving_waterfall(covered_volume_tokens_m=10.0)
    return res.model_dump()

@router.post("/sessions/{session_id}/whatif")
def whatif_endpoint(session_id: str, overrides: Optional[Dict[str, Any]] = None):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    run_state = sess.run_records.get("latest")
    if not run_state:
        raise HTTPException(status_code=400, detail="Cannot run what-if before initial run")

    res = execute_whatif_recompute(base_state=run_state, overrides=overrides)
    return res.model_dump()

@router.post("/sessions/{session_id}/constraints/parse")
def parse_constraints_endpoint(session_id: str, body: Dict[str, str]):
    text = body.get("text", "")
    parsed = parse_constraints(text)
    return parsed.model_dump()

@router.put("/sessions/{session_id}/constraints")
def update_constraints_endpoint(session_id: str, body: Dict[str, str]):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    text = body.get("text", "")
    parsed = parse_constraints(text)
    sess.inputs["constraints"] = parsed
    return parsed.model_dump()

@router.put("/sessions/{session_id}/constraints/structured")
def update_structured_constraints_endpoint(session_id: str, body: Dict[str, Any]):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    from stampede.stages.constraints_parse import ParsedConstraints, ConstraintItem
    items = []
    for it in body.get("items", []):
        items.append(ConstraintItem(**it))
    parsed = ParsedConstraints(
        items=items,
        unparsed_remainder=body.get("unparsed_remainder", []),
        raw_text=body.get("raw_text", ""),
        method="user_confirmed"
    )
    sess.inputs["constraints"] = parsed
    return parsed.model_dump()

@router.get("/sessions/{session_id}/constraints")
def get_constraints_endpoint(session_id: str):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    c = sess.inputs.get("constraints")
    if not c:
        return {"items": [], "unparsed_remainder": [], "raw_text": "", "method": "none"}
    return c.model_dump() if hasattr(c, "model_dump") else c

@router.get("/sessions/{session_id}/plan")
def get_plan_endpoint(session_id: str):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    run_state = sess.run_records.get("latest") or sess.session_cache
    if "planner" in run_state:
        return run_state["planner"]
    raise HTTPException(status_code=404, detail="No plan generated yet")

@router.post("/sessions/{session_id}/quotes/parse")
def parse_quotes_endpoint(session_id: str, body: Dict[str, str]):
    text = body.get("text", "")
    validate_quote_text_length(len(text))
    parsed = parse_quotes_text(text)
    return [q.model_dump() for q in parsed]

@router.post("/sessions/{session_id}/rfq/render")
def render_rfq_endpoint(session_id: str):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    run_state = sess.run_records.get("latest")
    if not run_state or "rfq" not in run_state:
        raise HTTPException(status_code=400, detail="No RFQ generated yet")
    return {"email_text": run_state["rfq"].get("email_text", "")}

@router.get("/models")
def list_models():
    return {
        "incumbents": [
            {"id": "openai/gpt-4o", "name": "GPT-4o", "cost_per_mtok": 5.00},
            {"id": "anthropic/claude-3-5-sonnet", "name": "Claude 3.5 Sonnet", "cost_per_mtok": 3.00}
        ],
        "candidates": [
            {"id": "meta-llama-3-70b-instruct", "name": "Llama 3 70B Instruct", "cost_per_mtok": 0.79},
            {"id": "mistral-large-2407", "name": "Mistral Large", "cost_per_mtok": 2.00},
            {"id": "deepseek/deepseek-chat", "name": "DeepSeek Chat", "cost_per_mtok": 0.14}
        ]
    }

@router.get("/budget")
def get_budget_endpoint():
    return {
        "session_cap_usd": settings.session_cap_usd,
        "daily_cap_usd": settings.daily_cap_usd,
        "global_daily_spend_usd": global_cost_ledger.get_daily_spend(),
        "kill_switch_active": settings.kill_switch_active
    }

@router.post("/seller/uplift")
def seller_uplift_endpoint(request: Request, body: Optional[Dict[str, Any]] = None):
    ip = request.client.host if request.client else "127.0.0.1"
    if not rate_limiter.check_read(ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    body = body or {}
    report = compute_seller_uplift(
        capacity_params=body.get("capacity_params"),
        demand_params=body.get("demand_params"),
        committed_share=body.get("committed_share", 0.70),
        forecast_error=body.get("forecast_error", 0.20)
    )
    return report.model_dump()

@router.post("/sessions/{session_id}/explain")
def explain_endpoint(session_id: str, body: Optional[Dict[str, Any]] = None):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    body = body or {}
    target = body.get("target", "net_discount")
    res = generate_shapley_explanation(target=target)
    return res.model_dump()
