from pathlib import Path
from typing import Dict, List, Any
from parity.gateway import LLMGateway
from parity.agent.corruption_builder import generate_corruption_suite
from parity.agent.parser_wrapper import evaluate_corruption_suite
from parity.agent.core_planner import (
    ProcurementRequirement,
    BuyerConstraints,
    optimize_procurement_plan
)
from parity.agent.loop import compare_parity_agent_vs_core
from parity.agent.grounding import (
    verify_narrative_grounding,
    generate_grounded_procurement_narrative
)
from parity.io import read_json, write_json_atomic

def run_procurement_module(
    matrix_path: Path = Path("data/parity/substitutability_matrix.json"),
    output_path: Path = Path("data/parity/procurement_results.json"),
    test_seed: int = 1337
) -> Dict[str, Any]:
    sub_data = read_json(matrix_path)
    sub_matrix = sub_data.get("matrix", {})

    test_corruption_suite = generate_corruption_suite(seed=test_seed)
    corruption_eval = evaluate_corruption_suite(test_corruption_suite)

    reqs = [
        ProcurementRequirement("json_extraction", 50.0, "openai/gpt-4o"),
        ProcurementRequirement("arithmetic_reasoning", 80.0, "openai/gpt-4o"),
        ProcurementRequirement("ticket_classification", 40.0, "openai/gpt-4o"),
        ProcurementRequirement("constraint_rewrite", 60.0, "anthropic/claude-3.5-sonnet")
    ]
    constraints = BuyerConstraints(
        spend_ceiling_usd=1200.0,
        excluded_providers=["Mistral"],
        max_provider_share=0.50
    )

    core_res = optimize_procurement_plan(
        requirements=reqs,
        constraints=constraints,
        substitutability_matrix=sub_matrix
    )

    narrative = generate_grounded_procurement_narrative(core_res)
    grounding_eval = verify_narrative_grounding(narrative, core_res)

    gateway = LLMGateway(offline=True)
    sample_scenarios = [
        {
            "scenario_id": "sc_01",
            "usage_csv": "date,model,prompt_tokens,completion_tokens,total_tokens,cost\n2026-08-01,openai/gpt-4o,1000,500,1500,0.01",
            "notes": "Expanding European cluster deployment by +35% in month 2",
            "spend_ceiling": 1200.0
        }
    ]
    agent_comparison = compare_parity_agent_vs_core(
        gateway=gateway,
        scenarios=sample_scenarios,
        sub_matrix=sub_matrix
    )

    metrics = {
        "G23_procurement_outperformance_vs_baseline": core_res["cost_outperformance_pct"],
        "G24_allocation_regret_ratio": core_res["regret_ratio"],
        "G25_downside_risk_containment": core_res["spend_ceiling_compliant"],
        "G26_provider_concentration_limit": core_res["max_provider_share"],
        "G27_numeric_grounding_accuracy": grounding_eval["accuracy"],
        "G28_corrupted_csv_header_repair_rate": corruption_eval["header_repair_rate"],
        "G29_corrupted_csv_row_recovery_rate": corruption_eval["row_recovery_rate"]
    }

    payload = {
        "metrics": metrics,
        "planner_parity_core": core_res,
        "agent_parity_agent_comparison": agent_comparison,
        "grounding": {
            "narrative": narrative,
            "evaluation": grounding_eval
        },
        "csv_corruption_evaluation": corruption_eval,
        "extra_not_gated": {
            "provider_concentration_limit": core_res["max_provider_share"]
        }
    }

    write_json_atomic(output_path, payload)
    return payload

def run_agent_module(
    matrix_path: Path = Path("data/parity/substitutability_matrix.json"),
    output_path: Path = Path("data/parity/procurement_results.json"),
    test_seed: int = 1337
) -> Dict[str, Any]:
    return run_procurement_module(
        matrix_path=matrix_path,
        output_path=output_path,
        test_seed=test_seed
    )
