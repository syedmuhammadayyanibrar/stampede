import numpy as np
from dataclasses import dataclass, replace
from typing import Dict, List, Tuple, Optional
from models import ModelCalibration, MarketScenario, LiquidityCalibration
from liquidity import compute_resale_spread

@dataclass
class SimulationResult:
    calibration: ModelCalibration
    tenor_days: int
    num_paths: int
    time_steps: int
    dt: float
    time_grid: np.ndarray
    spot_paths: np.ndarray
    terminal_spot: np.ndarray
    utilization: np.ndarray
    shock_mask: np.ndarray
    resale_spread: np.ndarray
    realized_resale_price: np.ndarray
    gross_value_buyer: np.ndarray
    fair_forward_price: float
    buyer_pnl: np.ndarray
    seller_pnl: np.ndarray
    standard_error: float

def run_monte_carlo(
    calibration: ModelCalibration,
    tenor_days: int,
    num_paths: int = 15000,
    resale_window_days: int = 14,
    risk_free_rate: float = 0.04,
    random_seed: int = 42,
    scenario: Optional[MarketScenario] = None,
    liquidity_cal: Optional[LiquidityCalibration] = None
) -> SimulationResult:
    rng = np.random.default_rng(random_seed)
    time_years = tenor_days / 365.0
    steps = tenor_days
    dt = time_years / steps
    time_grid = np.linspace(0.0, time_years, steps + 1)
    
    z = rng.standard_normal(size=(num_paths, steps))
    if scenario is not None and scenario.hazard_multiplier and len(scenario.hazard_multiplier) == steps:
        mult = np.array(scenario.hazard_multiplier)
        poisson_rate = np.maximum(1e-8, calibration.hazard_rate_annual * dt * mult)
        arrivals = rng.poisson(lam=poisson_rate, size=(num_paths, steps))
    else:
        poisson_rate = max(1e-8, calibration.hazard_rate_annual * dt)
        arrivals = rng.poisson(lam=poisson_rate, size=(num_paths, steps))
    
    drift_step = (calibration.annual_drift - 0.5 * (calibration.annual_volatility ** 2)) * dt
    diffusion_step = calibration.annual_volatility * np.sqrt(dt) * z
    jump_penalty = np.log(max(1e-4, 1.0 - calibration.jump_mean))
    jump_step = arrivals * jump_penalty
    
    log_increments = drift_step + diffusion_step + jump_step
    log_paths = np.empty((num_paths, steps + 1), dtype=np.float64)
    log_paths[:, 0] = np.log(calibration.spot_price_initial)
    log_paths[:, 1:] = np.log(calibration.spot_price_initial) + np.cumsum(log_increments, axis=1)
    spot_paths = np.exp(log_paths)
    terminal_spot = spot_paths[:, -1]
    
    if scenario is not None and scenario.utilization_samples is not None:
        if len(scenario.utilization_samples) == num_paths:
            utilization = scenario.utilization_samples
        else:
            utilization = rng.choice(scenario.utilization_samples, size=num_paths, replace=True)
    else:
        utilization = rng.beta(a=5.0, b=2.0, size=num_paths)
    
    window_steps = min(resale_window_days, steps)
    shock_mask = np.sum(arrivals[:, -window_steps:], axis=1) > 0
    
    resale_spread = compute_resale_spread(
        calibration=calibration,
        shock_mask=shock_mask,
        utilization=utilization,
        scenario=scenario,
        liquidity_cal=liquidity_cal,
        rng=rng
    )
    realized_resale_price = terminal_spot * (1.0 - resale_spread)
    
    gross_value_buyer = terminal_spot * (utilization + (1.0 - utilization) * (1.0 - resale_spread))
    
    discount_factor = np.exp(-risk_free_rate * time_years)
    fair_forward_price = float(discount_factor * np.mean(gross_value_buyer))
    
    buyer_pnl = (gross_value_buyer * discount_factor) - fair_forward_price
    seller_pnl = fair_forward_price - (terminal_spot * discount_factor)
    
    sample_std = float(np.std(gross_value_buyer * discount_factor, ddof=1))
    standard_error = sample_std / np.sqrt(num_paths)
    
    return SimulationResult(
        calibration=calibration,
        tenor_days=tenor_days,
        num_paths=num_paths,
        time_steps=steps,
        dt=dt,
        time_grid=time_grid,
        spot_paths=spot_paths,
        terminal_spot=terminal_spot,
        utilization=utilization,
        shock_mask=shock_mask,
        resale_spread=resale_spread,
        realized_resale_price=realized_resale_price,
        gross_value_buyer=gross_value_buyer,
        fair_forward_price=fair_forward_price,
        buyer_pnl=buyer_pnl,
        seller_pnl=seller_pnl,
        standard_error=standard_error
    )

def compute_sensitivities(
    calibration: ModelCalibration,
    tenor_days: int,
    num_paths: int = 15000,
    random_seed: int = 42,
    scenario: Optional[MarketScenario] = None
) -> Dict[str, float]:
    base_res = run_monte_carlo(calibration, tenor_days, num_paths=num_paths, random_seed=random_seed, scenario=scenario)
    base_f0 = base_res.fair_forward_price
    
    h_s = 0.05 * calibration.spot_price_initial
    cal_s_up = replace(calibration, spot_price_initial=calibration.spot_price_initial + h_s)
    cal_s_down = replace(calibration, spot_price_initial=calibration.spot_price_initial - h_s)
    f0_s_up = run_monte_carlo(cal_s_up, tenor_days, num_paths=num_paths, random_seed=random_seed, scenario=scenario).fair_forward_price
    f0_s_down = run_monte_carlo(cal_s_down, tenor_days, num_paths=num_paths, random_seed=random_seed, scenario=scenario).fair_forward_price
    spot_price_sensitivity = (f0_s_up - f0_s_down) / (2.0 * h_s)
    
    h_lam = 0.10
    cal_lam_up = replace(calibration, hazard_rate_annual=calibration.hazard_rate_annual + h_lam)
    cal_lam_down = replace(calibration, hazard_rate_annual=max(0.01, calibration.hazard_rate_annual - h_lam))
    f0_lam_up = run_monte_carlo(cal_lam_up, tenor_days, num_paths=num_paths, random_seed=random_seed, scenario=scenario).fair_forward_price
    f0_lam_down = run_monte_carlo(cal_lam_down, tenor_days, num_paths=num_paths, random_seed=random_seed, scenario=scenario).fair_forward_price
    hazard_rate_sensitivity = (f0_lam_up - f0_lam_down) / (cal_lam_up.hazard_rate_annual - cal_lam_down.hazard_rate_annual)
    
    dt_days = 5
    t_up = tenor_days + dt_days
    t_down = max(5, tenor_days - dt_days)
    f0_t_up = run_monte_carlo(calibration, t_up, num_paths=num_paths, random_seed=random_seed, scenario=scenario).fair_forward_price
    f0_t_down = run_monte_carlo(calibration, t_down, num_paths=num_paths, random_seed=random_seed, scenario=scenario).fair_forward_price
    tenor_sensitivity_annual = (f0_t_up - f0_t_down) / ((t_up - t_down) / 365.0)
    tenor_sensitivity_per_day = (f0_t_up - f0_t_down) / (t_up - t_down)
    
    h_vol = 0.05
    cal_vol_up = replace(calibration, annual_volatility=calibration.annual_volatility + h_vol)
    cal_vol_down = replace(calibration, annual_volatility=max(0.01, calibration.annual_volatility - h_vol))
    f0_vol_up = run_monte_carlo(cal_vol_up, tenor_days, num_paths=num_paths, random_seed=random_seed, scenario=scenario).fair_forward_price
    f0_vol_down = run_monte_carlo(cal_vol_down, tenor_days, num_paths=num_paths, random_seed=random_seed, scenario=scenario).fair_forward_price
    volatility_sensitivity = (f0_vol_up - f0_vol_down) / (2.0 * h_vol)
    
    return {
        "fair_forward_price": base_f0,
        "spot_price_sensitivity": spot_price_sensitivity,
        "hazard_rate_sensitivity": hazard_rate_sensitivity,
        "tenor_sensitivity_annual": tenor_sensitivity_annual,
        "tenor_sensitivity_per_day": tenor_sensitivity_per_day,
        "volatility_sensitivity": volatility_sensitivity
    }

def convergence_analysis(
    calibration: ModelCalibration,
    tenor_days: int,
    path_counts: List[int] = None,
    random_seed: int = 42,
    scenario: Optional[MarketScenario] = None
) -> List[Dict[str, float]]:
    if path_counts is None:
        path_counts = [500, 1000, 2500, 5000, 10000, 20000]
    
    results = []
    for n in path_counts:
        res = run_monte_carlo(calibration, tenor_days, num_paths=n, random_seed=random_seed, scenario=scenario)
        ci_95 = 1.96 * res.standard_error
        results.append({
            "num_paths": n,
            "fair_forward_price": res.fair_forward_price,
            "standard_error": res.standard_error,
            "ci_95_lower": res.fair_forward_price - ci_95,
            "ci_95_upper": res.fair_forward_price + ci_95,
            "relative_error_pct": (res.standard_error / res.fair_forward_price) * 100.0
        })
    return results
