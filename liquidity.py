import numpy as np
from typing import Optional
from models import LiquidityCalibration, ModelCalibration, MarketScenario

def compute_resale_spread(
    calibration: ModelCalibration,
    shock_mask: np.ndarray,
    utilization: np.ndarray,
    scenario: Optional[MarketScenario] = None,
    liquidity_cal: Optional[LiquidityCalibration] = None,
    rng: Optional[np.random.Generator] = None
) -> np.ndarray:
    num_paths = len(shock_mask)
    if rng is None:
        rng = np.random.default_rng(42)
    
    if scenario is None or getattr(scenario, "contract_type", "specific") == "assumed":
        spread_noise_norm = rng.normal(loc=calibration.base_spread, scale=0.012, size=num_paths)
        spread_noise_shock = rng.normal(loc=calibration.shock_spread, scale=0.045, size=num_paths)
        spread_norm = np.clip(spread_noise_norm, 0.02, 0.15)
        spread_shock = np.clip(spread_noise_shock, 0.20, 0.60)
        return np.where(shock_mask, spread_shock, spread_norm)
    
    if liquidity_cal is None:
        liquidity_cal = LiquidityCalibration(base_spread=calibration.base_spread, shock_spread_target=calibration.shock_spread)
    
    if scenario.switch_share_samples is not None:
        if len(scenario.switch_share_samples) == num_paths:
            phi = scenario.switch_share_samples
        else:
            phi = rng.choice(scenario.switch_share_samples, size=num_paths, replace=True)
    else:
        phi = np.full(num_paths, scenario.switch_share)
    
    eff_phi = phi * (1.0 - scenario.conversion_rate)
    
    v_sell_normal = 1.0 - utilization
    v_sell_shock = eff_phi + (1.0 - eff_phi) * (1.0 - utilization)
    v_sell = np.where(shock_mask, v_sell_shock, v_sell_normal)
    
    r0 = 2.0 / 7.0
    excess_sell = np.maximum(0.0, v_sell - scenario.absorbing_depth - r0)
    
    ref_phi = 0.60
    ref_excess = max(1e-4, ref_phi + (1.0 - ref_phi) * r0 - r0)
    ref_ratio = ref_excess / liquidity_cal.daily_volume_ratio
    target_spread_delta = max(0.01, calibration.shock_spread - calibration.base_spread)
    kappa = target_spread_delta / (ref_ratio ** liquidity_cal.impact_exponent)
    
    ratio = excess_sell / liquidity_cal.daily_volume_ratio
    impact = kappa * (ratio ** liquidity_cal.impact_exponent)
    
    noise_norm = rng.normal(loc=0.0, scale=0.012, size=num_paths)
    noise_shock = rng.normal(loc=0.0, scale=0.040, size=num_paths)
    noise = np.where(shock_mask, noise_shock, noise_norm)
    
    raw_spread = calibration.base_spread + impact + noise
    return np.clip(raw_spread, 0.02, 0.85)
