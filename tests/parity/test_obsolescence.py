from pathlib import Path
import numpy as np
from parity.obsolescence.hazard import (
    fit_exponential_hazard,
    fit_weibull_hazard,
    cluster_bootstrap_hazard
)
from parity.obsolescence.price_path import (
    simulate_jump_diffusion_paths,
    compute_forecast_cone,
    compute_obsolescence_premium,
    check_obsolescence_premium_monotonicity
)
from parity.obsolescence.backtester import run_obsolescence_backtest

def test_exponential_hazard_fit() -> None:
    durs = [1.0, 2.0, 1.5, 0.5]
    events = [1, 1, 0, 1]
    res = fit_exponential_hazard(durs, events)
    assert res.model_type == "exponential"
    assert res.parameters["rate"] > 0.0

def test_weibull_hazard_fit() -> None:
    durs = [0.5, 1.0, 1.5, 2.0, 2.5]
    events = [1, 1, 1, 0, 1]
    res = fit_weibull_hazard(durs, events)
    assert res.model_type == "weibull"
    assert res.parameters["scale"] > 0.0
    assert res.parameters["shape"] > 0.0

def test_cluster_bootstrap_provider_minimum() -> None:
    clusters_low = {"prov_a": [(1.0, 1)], "prov_b": [(2.0, 1)]}
    res_low = cluster_bootstrap_hazard(clusters_low, min_clusters=6)
    assert res_low["status"] == "INCONCLUSIVE"

    clusters_full = {f"prov_{i}": [(1.0 + i*0.2, 1)] for i in range(6)}
    res_full = cluster_bootstrap_hazard(clusters_full, min_clusters=6, num_bootstrap=50)
    assert res_full["status"] == "PASS"
    assert len(res_full["ci_95"]) == 2

def test_jump_diffusion_simulation() -> None:
    paths, terminal, has_jump = simulate_jump_diffusion_paths(
        spot_initial=5.00,
        drift=-0.20,
        volatility=0.25,
        hazard_rate=1.0,
        jump_mean=0.40,
        tenor_days=30,
        num_paths=100
    )
    assert paths.shape == (100, 31)
    assert len(terminal) == 100
    assert np.all(terminal > 0.0)

def test_forecast_cone_bounds() -> None:
    paths = np.array([
        [1.0, 2.0],
        [1.0, 3.0],
        [1.0, 4.0],
        [1.0, 5.0]
    ])
    low, med, high = compute_forecast_cone(paths, lower_pct=10.0, upper_pct=90.0)
    assert low[0] == med[0] == high[0] == 1.0
    assert low[1] < med[1] < high[1]

def test_obsolescence_premium_monotonicity() -> None:
    premiums = compute_obsolescence_premium(
        spot_initial=5.00,
        drift=-0.20,
        volatility=0.20,
        hazard_rates=[0.2, 0.5, 1.0, 1.8],
        jump_mean=0.40,
        tenor_days=90
    )
    assert check_obsolescence_premium_monotonicity(premiums) is True

def test_module_2_backtest_runner(tmp_path: Path) -> None:
    out_file = tmp_path / "obsolescence_curves.json"
    res = run_obsolescence_backtest(output_path=out_file)
    assert out_file.exists()
    metrics = res["metrics"]
    assert metrics["G08_hazard_brier_90d"] <= 0.18
    assert metrics["G09_price_path_cone_coverage"] >= 0.80
    assert metrics["G10_successor_timing_mae_days"] <= 45.0
    assert metrics["G11_depreciation_ranking_spearman"] >= 0.70
    assert metrics["G12_obsolescence_premium_monotonicity"] == 1.0
    assert metrics["distinct_providers"] >= 6
