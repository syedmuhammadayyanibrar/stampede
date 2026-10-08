import platform
import numpy as np
from stampede.whatif import execute_whatif_recompute
from stampede.stages.forecast import run_forecast_monte_carlo

def test_whatif_exactness_no_overrides():
    base_state = {
        "forecast": {"mean_daily_tokens": 1000.0, "total_tokens_q50": 90000.0},
        "sizing": {"optimal_sizing_tokens": {"value": 850.0}},
        "valuation": {"reservation_discount": {"value": 0.22}},
        "quotes_ranked": [],
        "plan": {"total_saving_usd": {"value": 1500.0}},
        "explanation": {"total_value_usd": {"value": 120.0}}
    }
    res = execute_whatif_recompute(base_state=base_state, overrides=None)
    assert res.touched_stages == []
    assert res.plan == base_state["plan"]
    assert res.recompute_ms < 2000.0

def test_whatif_recompute_with_overrides():
    base_state = {
        "forecast": {"mean_daily_tokens": 1000.0, "total_tokens_q50": 90000.0},
        "sizing": {"optimal_sizing_tokens": {"value": 850.0}},
        "valuation": {"reservation_discount": {"value": 0.22}},
        "quotes_ranked": [],
        "plan": {"total_saving_usd": {"value": 1500.0}},
        "explanation": {"total_value_usd": {"value": 120.0}},
        "history_tokens": [1000.0] * 30,
        "random_draws": {"normals": np.random.normal(0, 1, size=(90, 100)), "uniforms": np.random.uniform(0, 1, size=(90, 100))}
    }
    res = execute_whatif_recompute(base_state=base_state, overrides={"growth_multiplier": 1.25})
    assert "forecast" in res.touched_stages
    assert "sizing" in res.touched_stages
    assert res.recompute_ms < 2000.0

def test_whatif_override_changes_outputs_and_equals_scratch():
    rng = np.random.default_rng(42)
    n_paths = 4000
    normals = rng.normal(0, 1, size=(90, n_paths))
    uniforms = rng.uniform(0, 1, size=(90, n_paths))
    random_draws = {"normals": normals, "uniforms": uniforms}
    history = [100000.0] * 30

    base_fc = run_forecast_monte_carlo(history, days_ahead=90, random_draws=random_draws)
    base_state = {
        "forecast": base_fc.model_dump(),
        "sizing": {"optimal_sizing_tokens": {"value": 850.0}},
        "valuation": {"reservation_discount": {"value": 0.22}},
        "quotes_ranked": [],
        "plan": {"total_saving_usd": {"value": 1500.0}},
        "history_tokens": history,
        "random_draws": random_draws
    }

    res_whatif = execute_whatif_recompute(base_state=base_state, overrides={"growth_multiplier": 1.30})
    assert res_whatif.forecast["expected_total_m"]["value"] > base_state["forecast"]["expected_total_m"]["value"]

    scratch_history = [v * 1.30 for v in history]
    scratch_fc = run_forecast_monte_carlo(scratch_history, days_ahead=90, random_draws=random_draws)
    scratch_state = {
        "forecast": scratch_fc.model_dump(),
        "sizing": {"optimal_sizing_tokens": {"value": 850.0}},
        "valuation": {"reservation_discount": {"value": 0.22}},
        "quotes_ranked": [],
        "plan": {"total_saving_usd": {"value": 1500.0}},
        "history_tokens": scratch_history,
        "random_draws": random_draws
    }
    res_scratch = execute_whatif_recompute(base_state=scratch_state, overrides=None)

    diff = abs(res_whatif.forecast["expected_total_m"]["value"] - res_scratch.forecast["expected_total_m"]["value"])
    assert diff < 1e-6

    cpu_model = platform.processor() or platform.machine()
    assert cpu_model != ""
    assert res_whatif.recompute_ms < 2000.0
