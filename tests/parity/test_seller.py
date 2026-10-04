from pathlib import Path
from parity.seller.capacity import (
    compute_effective_utilization,
    compute_secondary_spread,
    evaluate_spread_compression
)
from parity.seller.runner import run_seller_module

def test_effective_utilization_monotonic() -> None:
    u0 = compute_effective_utilization(0.60, 0.0, 0.80)
    u25 = compute_effective_utilization(0.60, 0.25, 0.80)
    u50 = compute_effective_utilization(0.60, 0.50, 0.80)
    u100 = compute_effective_utilization(0.60, 1.0, 0.80)
    assert u0 == 0.60
    assert u0 < u25 < u50 < u100 <= 1.0

def test_cannibalization_dampener_reduces_absorption() -> None:
    u_no_damp = compute_effective_utilization(0.60, 0.50, 1.0)
    u_damped = compute_effective_utilization(0.60, 0.50, 0.80)
    assert u_damped <= u_no_damp

def test_spread_compression_at_50pct_exceeds_threshold() -> None:
    res = evaluate_spread_compression(
        primary_price=4.0,
        baseline_utilization=0.65,
        cannibalization_dampener=0.80
    )
    assert res["spread_compression_ratio"] >= 0.20
    assert res["spread_at_50pct"] < res["baseline_spread"]

def test_seller_runner_produces_curves(tmp_path: Path) -> None:
    out_file = tmp_path / "seller_curves.json"
    res = run_seller_module(output_path=out_file)
    assert out_file.exists()
    metrics = res["metrics"]
    assert metrics["G22_secondary_spread_compression_50pct"] >= 0.20
    assert len(res["curves"]["uptake_grid"]) == 11
    assert len(res["curves"]["spreads"]) == 11
