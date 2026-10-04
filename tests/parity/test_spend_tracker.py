import pytest
from pathlib import Path
from parity.spend_tracker import SpendTracker

def test_spend_tracker_lifecycle(tmp_path: Path) -> None:
    ledger = tmp_path / "test_ledger.json"
    tracker = SpendTracker(budget_usd_cap=1.00, sub_cap_ceiling_usd=0.20, ledger_path=ledger)
    assert tracker.get_cumulative_spend() == 0.0

    cost = tracker.record_call_spend("call_1", "openai/gpt-4o", prompt_tokens=1000, completion_tokens=500)
    assert cost > 0.0
    assert tracker.get_cumulative_spend() == cost

def test_spend_tracker_cap_enforcement(tmp_path: Path) -> None:
    ledger = tmp_path / "test_ledger_cap.json"
    tracker = SpendTracker(budget_usd_cap=0.01, sub_cap_ceiling_usd=0.005, ledger_path=ledger)

    with pytest.raises(RuntimeError, match="CEILING_CHECK_SUBCAP_EXCEEDED"):
        tracker.record_call_spend("call_over_ceiling", "openai/gpt-4o", prompt_tokens=5000, completion_tokens=1000, is_ceiling_check=True)

    with pytest.raises(RuntimeError, match="PARITY_BUDGET_EXCEEDED"):
        tracker.record_call_spend("call_over_budget", "openai/gpt-4o", prompt_tokens=10000, completion_tokens=5000, is_ceiling_check=False)
