from pathlib import Path
from parity.substitutability.engine import (
    compute_wilson_ci,
    compute_posterior_beta,
    probability_non_inferior,
    check_sequential_stopping,
    compute_effective_cost,
    compute_spearman_rho,
    compute_brier_score
)
from parity.substitutability.runner import run_substitutability_module

def test_wilson_confidence_interval() -> None:
    low, high = compute_wilson_ci(45, 50, confidence=0.95)
    assert 0.0 <= low < high <= 1.0
    assert 0.75 <= low <= 0.85
    assert 0.94 <= high <= 0.98

def test_bayesian_posterior_updating() -> None:
    alpha, beta = compute_posterior_beta(1.0, 1.0, successes=18, trials=20)
    assert alpha == 19.0
    assert beta == 3.0

def test_probability_non_inferior() -> None:
    p = probability_non_inferior(alpha_cand=25.0, beta_cand=3.0, alpha_inc=25.0, beta_inc=3.0, delta=0.05)
    assert 0.50 <= p <= 1.0

def test_sequential_stopping_logic() -> None:
    stop_early, dec_early = check_sequential_stopping(p_non_inf=0.99, current_n=10, min_n=15)
    assert stop_early is False

    stop_pass, dec_pass = check_sequential_stopping(p_non_inf=0.96, current_n=20, min_n=15)
    assert stop_pass is True
    assert dec_pass == "NON_INFERIOR"

    stop_fail, dec_fail = check_sequential_stopping(p_non_inf=0.02, current_n=20, min_n=15)
    assert stop_fail is True
    assert dec_fail == "INFERIOR"

def test_effective_cost_calculation() -> None:
    eff = compute_effective_cost(raw_task_cost_usd=0.002, theta_mean=0.80)
    assert abs(eff - 0.0025) < 1e-6

def test_spearman_rho() -> None:
    ranks1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    ranks2 = [1.1, 2.1, 3.2, 4.0, 5.1]
    assert compute_spearman_rho(ranks1, ranks2) > 0.99

def test_brier_score() -> None:
    preds = [0.9, 0.1, 0.8]
    targets = [1, 0, 1]
    assert compute_brier_score(preds, targets) < 0.10

def test_module_1_runner_generates_matrix(tmp_path: Path) -> None:
    out_file = tmp_path / "substitutability_matrix.json"
    res = run_substitutability_module(output_path=out_file)
    assert out_file.exists()
    assert "matrix" in res
    assert "metrics" in res
    assert res["metrics"]["G01_judge_accuracy_kappa"] >= 0.70
    assert res["metrics"]["G02_judge_swap_flip_rate"] <= 0.10
    assert res["metrics"]["G03_sequential_stopping_efficiency"] >= 0.25
    assert res["metrics"]["G04_holdout_calibration_brier"] <= 0.15
    assert res["metrics"]["G05_cost_ranking_monotonicity"] >= 0.85
    assert res["metrics"]["G06_effective_cost_ratio_mae"] <= 0.08
    assert res["metrics"]["G07_multi_turn_degradation_recall"] >= 0.80
