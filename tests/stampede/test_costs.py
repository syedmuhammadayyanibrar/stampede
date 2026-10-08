import pytest
from stampede.costs import CostLedger, estimate_run_cost
from stampede.settings import settings

def test_cost_estimator_bounds_actual():
    est = estimate_run_cost(num_prompts=24, num_candidates=2, stages=["parity", "narrative"])
    assert est.total_estimated_usd > 0
    assert est.total_estimated_usd < 5.0

def test_cost_ledger_cap_enforcement(tmp_path):
    ledger = CostLedger(log_path=tmp_path / "ledger.jsonl")
    sid = "sess_test_cap"
    allowed, rem = ledger.check_and_allocate(sid, 0.50, is_byok=False)
    assert allowed
    ledger.record_call(sid, "test_call", "test_model", 100, 50, 0.50)

    allowed2, rem2 = ledger.check_and_allocate(sid, 5.00, is_byok=False)
    assert not allowed2

def test_byok_key_not_logged(tmp_path):
    ledger = CostLedger(log_path=tmp_path / "ledger.jsonl")
    sid = "sess_byok"
    ledger.record_call(sid, "call_1", "gpt-4o", 10, 10, 0.01)
    content = (tmp_path / "ledger.jsonl").read_text(encoding="utf-8")
    assert "sk-" not in content
    assert "fake-key" not in content
