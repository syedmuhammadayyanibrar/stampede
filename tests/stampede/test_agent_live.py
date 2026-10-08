from typing import List, Dict, Any
from stampede.agent_live import execute_agent_loop, evaluate_read_only_tool
from stampede.types import Quantity, Provenance
from tests.support.fake_models import FakeGateway

def test_agent_loop_without_key_falls_back_to_planner():
    session_data = {
        "forecast": {"mean": 1000},
        "plan": {"total_spend": 5000}
    }
    res = execute_agent_loop(session_data=session_data, gateway=None)
    assert not res.is_agent_executed
    assert "planner output, no LLM" in res.label
    assert len(res.steps) == 0

def test_agent_loop_tool_call_cap_and_streaming():
    gw = FakeGateway(api_key="fake-test-key")

    events_streamed: List[Dict[str, Any]] = []
    def callback(evt: Dict[str, Any]) -> None:
        events_streamed.append(evt)

    session_data = {
        "forecast": {"mean": Quantity(id="fc.mean", value=1200.0, unit="tokens", provenance=Provenance.FITTED, source="test")},
        "parity": {"theta": Quantity(id="par.theta", value=0.92, unit="probability", provenance=Provenance.MEASURED_LIVE, source="test")},
        "plan": {"risk_adjusted_saving_usd": Quantity(id="plan.saving", value=3400.0, unit="usd", provenance=Provenance.FITTED, source="test")},
        "quotes_ranked": [],
        "valuation": {},
        "rfq": {},
        "exit_recovery": {}
    }

    res = execute_agent_loop(
        session_data=session_data,
        gateway=gw,
        event_callback=callback,
        max_steps=12
    )

    assert res.is_agent_executed is True
    assert len(res.steps) <= 12
    assert len(events_streamed) == len(res.steps)
    for step in res.steps:
        assert step.step_number > 0
        assert step.tool != ""
        assert step.summary != ""
        assert isinstance(step.quantity_ids, list)

def test_agent_read_only_tools_and_injection():
    session_data = {
        "plan": {"risk_adjusted_saving_usd": 2500.0}
    }
    injection_tool = "delete_session_and_wipe_disk"
    res = evaluate_read_only_tool(injection_tool, {}, session_data)
    assert "error" in res

    injection_tool_2 = "spend_unlimited_credits"
    res_2 = evaluate_read_only_tool(injection_tool_2, {}, session_data)
    assert "error" in res_2

def test_solver_stands_rule_worse_saving():
    gw = FakeGateway(api_key="fake-test-key")

    session_data = {
        "plan": {"risk_adjusted_saving_usd": 5000.0}
    }
    worse_candidate = {
        "risk_adjusted_saving_usd": 3000.0,
        "has_constraint_violation": False
    }

    res = execute_agent_loop(
        session_data=session_data,
        gateway=gw,
        candidate_plan=worse_candidate
    )

    assert res.label == "solver"
    assert "Solver optimum stands" in (res.explanation or "")

def test_solver_stands_rule_constraint_violation():
    gw = FakeGateway(api_key="fake-test-key")

    session_data = {
        "plan": {"risk_adjusted_saving_usd": 5000.0}
    }
    violating_candidate = {
        "risk_adjusted_saving_usd": 7000.0,
        "has_constraint_violation": True
    }

    res = execute_agent_loop(
        session_data=session_data,
        gateway=gw,
        candidate_plan=violating_candidate
    )

    assert res.label == "solver"
    assert "violated hard constraints" in (res.explanation or "")

def test_agent_plan_accepted_when_optimal():
    gw = FakeGateway(api_key="fake-test-key")

    session_data = {
        "plan": {"risk_adjusted_saving_usd": 5000.0}
    }
    better_candidate = {
        "risk_adjusted_saving_usd": 5500.0,
        "has_constraint_violation": False
    }

    res = execute_agent_loop(
        session_data=session_data,
        gateway=gw,
        candidate_plan=better_candidate
    )

    assert res.label == "agent"
    assert res.plan == better_candidate
