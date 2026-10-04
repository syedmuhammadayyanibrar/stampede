import pytest
import numpy as np
from models import CALIBRATED_MODELS, MarketScenario, LiquidityCalibration
from engine import run_monte_carlo, compute_sensitivities
from crunch_experiment import run_liquidity_crunch_experiment
from liquidity import compute_resale_spread

def test_baseline_regression():
    cal = CALIBRATED_MODELS["openai_gpt_tier"]
    res = run_liquidity_crunch_experiment(
        calibration=cal,
        tenor_days=90,
        num_paths=25000,
        resale_window_days=14,
        random_seed=42
    )
    assert 3.60 <= res.fair_forward_price <= 3.66
    assert 10.2 <= res.lcr_benchmark <= 12.0
    assert 6.20 <= res.lcr_spread <= 6.45
    assert res.mean_resale_normal > res.mean_resale_shock

def test_sensitivities_signs():
    cal = CALIBRATED_MODELS["openai_gpt_tier"]
    sens = compute_sensitivities(cal, tenor_days=90, num_paths=10000, random_seed=42)
    assert sens["spot_price_sensitivity"] > 0.0
    assert sens["hazard_rate_sensitivity"] < 0.0
    assert sens["tenor_sensitivity_annual"] < 0.0

def test_hazard_multiplier_flat_equivalence():
    cal = CALIBRATED_MODELS["openai_gpt_tier"]
    sim1 = run_monte_carlo(cal, tenor_days=90, num_paths=5000, random_seed=42)
    sc = MarketScenario(hazard_multiplier=tuple([1.0] * 90), contract_type="assumed")
    sim2 = run_monte_carlo(cal, tenor_days=90, num_paths=5000, random_seed=42, scenario=sc)
    assert abs(sim1.fair_forward_price - sim2.fair_forward_price) < 1e-4

def test_liquidity_spread_monotonic():
    cal = CALIBRATED_MODELS["openai_gpt_tier"]
    shock_mask = np.ones(1000, dtype=bool)
    util = np.full(1000, 0.70)
    
    sc_low = MarketScenario(switch_share=0.30, absorbing_depth=0.0)
    sc_high = MarketScenario(switch_share=0.85, absorbing_depth=0.0)
    sc_absorb = MarketScenario(switch_share=0.85, absorbing_depth=0.30)
    
    sp_low = compute_resale_spread(cal, shock_mask, util, scenario=sc_low)
    sp_high = compute_resale_spread(cal, shock_mask, util, scenario=sc_high)
    sp_absorb = compute_resale_spread(cal, shock_mask, util, scenario=sc_absorb)
    
    assert np.mean(sp_high) > np.mean(sp_low)
    assert np.mean(sp_high) > np.mean(sp_absorb)
