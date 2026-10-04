from pathlib import Path
from parity.agent.corruption_builder import generate_corruption_suite
from parity.agent.parser_wrapper import evaluate_corruption_suite, parse_corrupted_csv
from parity.agent.procurement import (
    ProcurementRequirement,
    BuyerConstraints,
    optimize_procurement_portfolio
)
from parity.agent.grounding import (
    extract_numbers_from_text,
    verify_narrative_grounding,
    generate_grounded_procurement_narrative
)
from parity.agent.runner import run_agent_module

def test_corrupted_csv_evaluation() -> None:
    suite = generate_corruption_suite(seed=1337)
    res = evaluate_corruption_suite(suite)
    assert res["header_repair_rate"] >= 0.90
    assert res["row_recovery_rate"] >= 0.85

def test_procurement_optimization_constraints() -> None:
    reqs = [
        ProcurementRequirement("code_generation", 40.0, "openai/gpt-4o"),
        ProcurementRequirement("structured_extraction", 60.0, "openai/gpt-4o")
    ]
    constraints = BuyerConstraints(
        spend_ceiling_usd=800.0,
        excluded_providers=["Mistral"],
        max_provider_share=0.50
    )
    matrix = {
        "code_generation": {"openai/gpt-4o-mini": {"decision": "NON_INFERIOR", "p_non_inferior": 0.95, "effective_cost_usd": 0.55}},
        "structured_extraction": {"deepseek/deepseek-chat": {"decision": "NON_INFERIOR", "p_non_inferior": 0.92, "effective_cost_usd": 1.30}}
    }
    res = optimize_procurement_portfolio(reqs, constraints, matrix)
    assert res["spend_ceiling_compliant"] == 1.0
    assert res["max_provider_share"] <= 0.50
    assert res["cost_outperformance_pct"] >= 0.05
    assert res["regret_ratio"] <= 0.08

def test_grounding_guard_catches_hallucinations() -> None:
    ground_truth = {"total_spend": 500.0, "savings_pct": 25.5}
    grounded_text = "Analysis shows total spend is $500.00 with 25.50% savings."
    eval_good = verify_narrative_grounding(grounded_text, ground_truth)
    assert eval_good["is_grounded"] is True
    assert eval_good["accuracy"] == 1.0

    hallucinated_text = "Analysis shows total spend is $9999.00 with 99.00% savings."
    eval_bad = verify_narrative_grounding(hallucinated_text, ground_truth)
    assert eval_bad["is_grounded"] is False
    assert eval_bad["accuracy"] < 1.0
    assert len(eval_bad["unverified_numbers"]) > 0

def test_agent_runner(tmp_path: Path) -> None:
    out_file = tmp_path / "procurement_results.json"
    res = run_agent_module(output_path=out_file)
    assert out_file.exists()
    metrics = res["metrics"]
    assert metrics["G23_procurement_outperformance_vs_baseline"] >= 0.05
    assert metrics["G24_allocation_regret_ratio"] <= 0.08
    assert metrics["G25_downside_risk_containment"] == 1.0
    assert metrics["G26_provider_concentration_limit"] <= 0.50
    assert metrics["G27_numeric_grounding_accuracy"] == 1.0
    assert metrics["G28_corrupted_csv_header_repair_rate"] >= 0.90
    assert metrics["G29_corrupted_csv_row_recovery_rate"] >= 0.85
