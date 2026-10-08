# Stampede Live Compliance Matrix

This document tracks implementation and verification status across all system requirements and safety rails.

| Requirement Item | Status | File Path | Proving Command |
| :--- | :--- | :--- | :--- |
| cost estimate before run | PARTIAL | `stampede/costs.py`, `stampede/api/routes.py` | `python -m pytest tests/stampede/test_costs.py` |
| session and daily caps | IMPLEMENTED | `stampede/costs.py`, `stampede/settings.py` | `python -m pytest tests/stampede/test_costs.py` |
| kill switch | PARTIAL | `stampede/api/routes.py`, `stampede/settings.py` | `python -m pytest tests/stampede/test_sessions_privacy.py` |
| BYOK | PARTIAL | `stampede/api/routes.py`, `stampede/sessions.py` | `python -m pytest tests/stampede/test_sessions_privacy.py` |
| delete my data | PARTIAL | `stampede/api/routes.py`, `stampede/sessions.py` | `python -m pytest tests/stampede/test_sessions_privacy.py` |
| rate limits | IMPLEMENTED | `stampede/api/security.py` | `python -m pytest tests/stampede/test_sse.py` |
| sequential parity with streamed posterior | PARTIAL | `stampede/stages/parity_live.py`, `stampede/events.py` | `python -m pytest tests/stampede/test_parity_live.py` |
| evidence endpoint and drawer | MISSING | `stampede/api/routes.py`, `web/index.html` | `python -m pytest tests/stampede/test_evidence.py` |
| judged versus checked mode | IMPLEMENTED | `stampede/stages/workload.py`, `stampede/stages/judge_adjust.py` | `python -m pytest tests/stampede/test_judge_adjust.py` |
| all six verifier types | PARTIAL | `stampede/stages/workload.py` | `python -m pytest tests/stampede/test_verifiers_all.py` |
| reservation prices | PARTIAL | `stampede/stages/valuation_live.py` | `python -m pytest tests/stampede/test_reservation.py` |
| LLM quote parser with evidence quotes | PARTIAL | `stampede/stages/quotes_parse.py` | `python -m pytest tests/stampede/test_quotes_parse.py` |
| waterfall decomposition | MISSING | `stampede/stages/waterfall.py` | `python -m pytest tests/stampede/test_waterfall.py` |
| LLM constraint parser | PARTIAL | `stampede/stages/constraints_parse.py` | `python -m pytest tests/stampede/test_constraints_planner.py` |
| LLM ingestion fallback with invariants | PARTIAL | `stampede/stages/ingest.py` | `python -m pytest tests/stampede/test_ingest.py` |
| planner with rejected-option reasons | IMPLEMENTED | `stampede/stages/planner.py` | `python -m pytest tests/stampede/test_constraints_planner.py` |
| RFQ | IMPLEMENTED | `stampede/stages/rfq.py` | `python -m pytest tests/stampede/test_whatif.py` |
| grounded narrative | IMPLEMENTED | `stampede/stages/narrative.py` | `python -m pytest tests/stampede/test_grounding_live.py` |
| exit route with two mechanisms | IMPLEMENTED | `stampede/stages/exit_route.py` | `python -m pytest tests/stampede/test_whatif.py` |
| live agent with streamed tool trace | PARTIAL | `stampede/agent_live.py` | `python -m pytest tests/stampede/test_agent_live.py` |
| seller view | IMPLEMENTED | `stampede/stages/seller_view.py` | `python -m pytest tests/stampede/test_whatif.py` |
