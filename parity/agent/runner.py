from pathlib import Path
from typing import Dict, List, Any
from parity.agent.corruption_builder import generate_corruption_suite
from parity.agent.parser_wrapper import evaluate_corruption_suite
from parity.agent.procurement import (
    ProcurementRequirement,
    BuyerConstraints,
    optimize_procurement_portfolio
)
from parity.agent.grounding import (
    verify_narrative_grounding,
    generate_grounded_procurement_narrative
)
from parity.io import read_json, write_json_atomic

def run_agent_module(
    matrix_path: Path = Path("data/parity/substitutability_matrix.json"),
    output_path: Path = Path("data/parity/procurement_results.json"),
    test_seed: int = 1337
) -> Dict[str, Any]:
    sub_data = read_json(matrix_path)
    sub_matrix = sub_data.get("matrix", {})

    test_corruption_suite = generate_corruption_suite(seed=test_seed)
    corruption_eval = evaluate_corruption_suite(test_corruption_suite)

    reqs = [
        ProcurementRequirement("code_generation", 50.0, "openai/gpt-4o"),
        ProcurementRequirement("structured_extraction", 80.0, "openai/gpt-4o"),
        ProcurementRequirement("reasoning_math", 40.0, "openai/gpt-4o"),
        ProcurementRequirement("translation", 60.0, "anthropic/claude-3.5-sonnet")
    ]
    constraints = BuyerConstraints(
        spend_ceiling_usd=1200.0,
        excluded_providers=["Mistral"],
        max_provider_share=0.50
    )

    opt_res = optimize_procurement_portfolio(
        requirements=reqs,
        constraints=constraints,
        substitutability_matrix=sub_matrix
    )

    narrative = generate_grounded_procurement_narrative(opt_res)
    grounding_eval = verify_narrative_grounding(narrative, opt_res)

    metrics = {
        "G23_procurement_outperformance_vs_baseline": opt_res["cost_outperformance_pct"],
        "G24_allocation_regret_ratio": opt_res["regret_ratio"],
        "G25_downside_risk_containment": opt_res["spend_ceiling_compliant"],
        "G26_provider_concentration_limit": opt_res["max_provider_share"],
        "G27_numeric_grounding_accuracy": grounding_eval["accuracy"],
        "G28_corrupted_csv_header_repair_rate": corruption_eval["header_repair_rate"],
        "G29_corrupted_csv_row_recovery_rate": corruption_eval["row_recovery_rate"]
    }

    payload = {
        "metrics": metrics,
        "optimization": opt_res,
        "grounding": {
            "narrative": narrative,
            "evaluation": grounding_eval
        },
        "csv_corruption_evaluation": corruption_eval
    }

    write_json_atomic(output_path, payload)
    return payload
