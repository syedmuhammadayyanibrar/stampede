import numpy as np
from typing import Dict, Any, List
from models import ModelCalibration, CALIBRATED_MODELS, MarketScenario
from engine import run_monte_carlo
from crunch_experiment import run_liquidity_crunch_experiment

def price_specific_forward(calibration: ModelCalibration, tenor_days: int = 90, num_paths: int = 15000, random_seed: int = 42) -> Dict[str, Any]:
    sc = MarketScenario(contract_type="specific")
    res = run_monte_carlo(calibration, tenor_days, num_paths=num_paths, random_seed=random_seed, scenario=sc)
    s0 = calibration.spot_price_initial
    disc_pct = ((res.fair_forward_price - s0) / s0) * 100.0
    return {
        "contract_type": "specific_model",
        "model": calibration.family_name,
        "tenor_days": tenor_days,
        "initial_spot": s0,
        "fair_forward_price": round(res.fair_forward_price, 3),
        "discount_to_spot_pct": round(disc_pct, 2),
        "standard_error": round(res.standard_error, 4)
    }

def price_best_in_class_forward(calibration: ModelCalibration, tenor_days: int = 90, num_paths: int = 15000, random_seed: int = 42) -> Dict[str, Any]:
    sc = MarketScenario(contract_type="best_in_class", switch_share=0.0)
    res = run_monte_carlo(calibration, tenor_days, num_paths=num_paths, random_seed=random_seed, scenario=sc)
    s0 = calibration.spot_price_initial
    premium_over_specific = 0.08 * s0
    bic_price = res.fair_forward_price + premium_over_specific
    disc_pct = ((bic_price - s0) / s0) * 100.0
    return {
        "contract_type": "best_in_class",
        "model": "Frontier Tier Dynamic Best-in-Class",
        "tenor_days": tenor_days,
        "initial_spot": s0,
        "fair_forward_price": round(bic_price, 3),
        "discount_to_spot_pct": round(disc_pct, 2),
        "premium_over_specific": round(premium_over_specific, 3),
        "crunch_exposure_risk": "Zero (contract automatically rolls to new frontier model)"
    }

def evaluate_upgrade_conversion(calibration: ModelCalibration = CALIBRATED_MODELS["openai_gpt_tier"], tenor_days: int = 90, num_paths: int = 15000, random_seed: int = 42) -> List[Dict[str, Any]]:
    empirical_phi = np.array([0.817, 0.416, 0.470, 0.094, 0.683, 1.000])
    rates = [0.0, 0.25, 0.50, 0.75, 1.0]
    results = []
    
    for r in rates:
        sc = MarketScenario(
            switch_share=float(np.mean(empirical_phi)),
            switch_share_samples=empirical_phi,
            conversion_rate=r,
            contract_type="specific"
        )
        exp_res = run_liquidity_crunch_experiment(
            calibration=calibration,
            tenor_days=tenor_days,
            num_paths=num_paths,
            random_seed=random_seed,
            scenario=sc
        )
        results.append({
            "conversion_rate_pct": round(r * 100, 1),
            "lcr_benchmark": round(exp_res.lcr_benchmark, 2),
            "lcr_spread": round(exp_res.lcr_spread, 2),
            "mean_resale_shock": round(exp_res.mean_resale_shock, 2),
            "shock_spread_pct": round(exp_res.resale_spread_shock * 100, 1),
            "shock_net_penalty": round(exp_res.fair_total_shock_penalty, 3)
        })
    return results
