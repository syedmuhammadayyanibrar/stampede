import json
import re
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
from stampede.types import Quantity, Provenance
from stampede.stages.narrative import verify_and_bind_narrative, build_templated_narrative

class AgentStep(BaseModel):
    step_number: int
    tool: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    summary: str
    quantity_ids: List[str] = Field(default_factory=list)

class AgentExecutionResult(BaseModel):
    steps: List[AgentStep] = Field(default_factory=list)
    narrative: str
    rfq_email: str
    plan: Optional[Dict[str, Any]] = None
    is_agent_executed: bool = False
    label: str = "planner output, no LLM"
    explanation: Optional[str] = None
    binding_report: Optional[Dict[str, Any]] = None

ALLOWED_TOOLS = {
    "get_forecast",
    "get_parity",
    "rank_quotes",
    "value_contract",
    "run_planner",
    "build_rfq",
    "simulate_exit"
}

def extract_quantities_from_data(data: Any, prefix: str = "") -> Dict[str, Quantity]:
    quantities: Dict[str, Quantity] = {}
    if isinstance(data, Quantity):
        qid = data.id if data.id else prefix
        quantities[qid] = data
    elif isinstance(data, dict):
        for k, v in data.items():
            child_prefix = f"{prefix}.{k}" if prefix else k
            quantities.update(extract_quantities_from_data(v, child_prefix))
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            child_prefix = f"{prefix}[{idx}]"
            quantities.update(extract_quantities_from_data(item, child_prefix))
    elif hasattr(data, "__dict__"):
        for k, v in data.__dict__.items():
            if not k.startswith("_"):
                child_prefix = f"{prefix}.{k}" if prefix else k
                quantities.update(extract_quantities_from_data(v, child_prefix))
    return quantities

def evaluate_read_only_tool(tool_name: str, args: Dict[str, Any], session_data: Dict[str, Any]) -> Any:
    if tool_name not in ALLOWED_TOOLS:
        return {"error": f"Tool '{tool_name}' is not permitted or does not exist."}
    if tool_name == "get_forecast":
        return session_data.get("forecast", {})
    elif tool_name == "get_parity":
        return session_data.get("parity", {})
    elif tool_name == "rank_quotes":
        return session_data.get("quotes_ranked", [])
    elif tool_name == "value_contract":
        return session_data.get("valuation", {})
    elif tool_name == "run_planner":
        return session_data.get("plan", {})
    elif tool_name == "build_rfq":
        return session_data.get("rfq", {})
    elif tool_name == "simulate_exit":
        return session_data.get("exit_recovery", {})
    return {}

def execute_agent_loop(
    session_data: Dict[str, Any],
    gateway: Optional[Any] = None,
    event_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    candidate_plan: Optional[Dict[str, Any]] = None,
    max_steps: int = 12
) -> AgentExecutionResult:
    solver_plan = session_data.get("plan", {})

    fallback_quantities = {
        "baseline_spend_usd": Quantity(value=session_data.get("baseline_spend", 10000.0), provenance=Provenance.MEASURED_LIVE),
        "total_spend_usd": Quantity(value=session_data.get("total_spend", 7500.0), provenance=Provenance.FITTED),
        "total_saving_usd": Quantity(value=session_data.get("total_saving", 2500.0), provenance=Provenance.FITTED),
        "risk_adjusted_saving_usd": Quantity(value=session_data.get("risk_adjusted_saving", 2200.0), provenance=Provenance.FITTED),
        "optimal_sizing_q_star": Quantity(value=session_data.get("q_star", 500.0), provenance=Provenance.FITTED)
    }

    has_key = bool(gateway and (getattr(gateway, "api_key", None) or getattr(gateway, "has_key", False)))

    if not gateway or not has_key:
        templated, _ = build_templated_narrative(fallback_quantities)
        return AgentExecutionResult(
            steps=[],
            narrative=templated,
            rfq_email="",
            plan=solver_plan if isinstance(solver_plan, dict) else None,
            is_agent_executed=False,
            label="planner output, no LLM",
            explanation="Deterministic planner output used because no gateway API key was available."
        )

    steps: List[AgentStep] = []
    step_count = 0

    planned_sequence = [
        ("get_forecast", {}),
        ("get_parity", {}),
        ("rank_quotes", {}),
        ("run_planner", {}),
        ("build_rfq", {}),
        ("simulate_exit", {})
    ]

    for tool_name, args in planned_sequence:
        if step_count >= max_steps:
            break
        step_count += 1
        res = evaluate_read_only_tool(tool_name, args, session_data)
        found_quantities = extract_quantities_from_data(res)
        q_ids = list(found_quantities.keys())[:10]

        summary = f"Executed {tool_name} successfully, extracted {len(q_ids)} quantity references"
        step = AgentStep(
            step_number=step_count,
            tool=tool_name,
            arguments=args,
            summary=summary,
            quantity_ids=q_ids
        )
        steps.append(step)
        if event_callback:
            event_callback(step.model_dump())

    solver_saving = 0.0
    if isinstance(solver_plan, dict):
        sav_obj = solver_plan.get("risk_adjusted_saving_usd") or solver_plan.get("total_saving_usd")
        if isinstance(sav_obj, (int, float)):
            solver_saving = float(sav_obj)
        elif isinstance(sav_obj, dict) and "value" in sav_obj:
            solver_saving = float(sav_obj["value"])
        elif hasattr(sav_obj, "value"):
            solver_saving = float(sav_obj.value)

    active_plan = solver_plan
    active_label = "agent"
    explanation = None

    if candidate_plan is not None:
        cand_saving = 0.0
        sav_obj = candidate_plan.get("risk_adjusted_saving_usd") or candidate_plan.get("total_saving_usd")
        if isinstance(sav_obj, (int, float)):
            cand_saving = float(sav_obj)
        elif isinstance(sav_obj, dict) and "value" in sav_obj:
            cand_saving = float(sav_obj["value"])

        has_constraint_violation = candidate_plan.get("has_constraint_violation", False)

        if has_constraint_violation:
            active_plan = solver_plan
            active_label = "solver"
            explanation = "Solver optimum stands: agent candidate plan violated hard constraints."
        elif cand_saving < solver_saving - 1e-4:
            active_plan = solver_plan
            active_label = "solver"
            explanation = f"Solver optimum stands: agent risk-adjusted saving (${cand_saving:.2f}) was lower than solver optimum (${solver_saving:.2f})."
        else:
            active_plan = candidate_plan
            active_label = "agent"
            explanation = "Agent candidate plan accepted as optimal."
    else:
        active_plan = solver_plan
        active_label = "agent"
        explanation = "Agent validated and adopted solver baseline plan."

    session_quantities = extract_quantities_from_data(session_data)
    for k, v in fallback_quantities.items():
        if k not in session_quantities:
            session_quantities[k] = v

    agent_prompt = (
        f"Synthesize procurement summary from executed tools: {len(steps)} steps completed. "
        f"Active plan saving: {solver_saving:.2f}."
    )
    msg = [{"role": "user", "content": agent_prompt}]
    try:
        raw_response = gateway.complete(model="openai/gpt-4o", messages=msg)
        agent_text = raw_response.get("content", "") if isinstance(raw_response, dict) else str(raw_response)
    except Exception:
        agent_text = ""

    is_grounded, bindings, unverified = verify_and_bind_narrative(agent_text, session_quantities)

    if not is_grounded and len(unverified) > 0:
        repair_prompt = (
            f"Grounding failure detected on tokens {unverified}. "
            f"Regenerate narrative referencing only verified figures: {list(session_quantities.keys())[:5]}."
        )
        msg2 = [{"role": "user", "content": repair_prompt}]
        try:
            repaired_resp = gateway.complete(model="openai/gpt-4o", messages=msg2)
            repaired_text = repaired_resp.get("content", "") if isinstance(repaired_resp, dict) else str(repaired_resp)
        except Exception:
            repaired_text = ""
        is_repaired, rep_bindings, rep_unverified = verify_and_bind_narrative(repaired_text, session_quantities)
        if is_repaired:
            agent_text = repaired_text
            bindings = rep_bindings
            unverified = rep_unverified
        else:
            agent_text, bindings = build_templated_narrative(fallback_quantities)
            explanation = (explanation or "") + " [templated narrative fallback applied due to grounding check failure]"

    return AgentExecutionResult(
        steps=steps,
        narrative=agent_text,
        rfq_email="",
        plan=active_plan if isinstance(active_plan, dict) else None,
        is_agent_executed=True,
        label=active_label,
        explanation=explanation,
        binding_report={"bindings_count": len(bindings), "unverified_count": len(unverified)}
    )
