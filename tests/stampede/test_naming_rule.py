from pathlib import Path
from stampede.audit import audit_components

def test_naming_rule_gateway_calls():
    records = audit_components()
    violations = []

    for r in records:
        name = r["component"].lower()
        kind = r["kind"]
        calls = r["calls_gateway"]

        is_named_agent = (name == "agent" or name.endswith("_agent") or name.startswith("agent_") or "execute_agent" in name) and not name.startswith("test_")
        is_named_judge = (name == "judge" or name.endswith("_judge") or name.startswith("judge_") or "run_judge" in name) and "adjust" not in name and "load_judge" not in name and "format_" not in name and "parse_" not in name and not name.startswith("test_")
        is_named_model_call = "model_call" in name and not name.startswith("test_")

        if (is_named_agent or is_named_judge or is_named_model_call) and not calls:
            violations.append(f"Component '{r['component']}' named agent/judge/model_call in {r['file']} does not call gateway.")

    assert not violations, "\n".join(violations)

def test_gateway_component_never_labels_output_deterministic():
    records = audit_components()
    violations = []

    for r in records:
        if r["classification"] == "LLM":
            if "deterministic" in r["component"].lower():
                violations.append(f"Component '{r['component']}' calls gateway but has deterministic in name.")

    assert not violations, "\n".join(violations)
