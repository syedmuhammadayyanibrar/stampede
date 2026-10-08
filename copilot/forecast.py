import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
from .plans import PlanEvent

@dataclass
class ForecastResult:
    horizon_days: int
    days_grid: List[int]
    p10_daily_m: List[float]
    median_daily_m: List[float]
    p90_daily_m: List[float]
    expected_total_demand_m: float
    p10_total_demand_m: float
    p50_total_demand_m: float
    p90_total_demand_m: float
    scenario_total_demands: np.ndarray

def generate_demand_forecast(
    historical_daily_m: List[float],
    plan_events: List[PlanEvent],
    horizon_days: int = 90,
    num_scenarios: int = 5000,
    random_seed: int = 42,
    random_draws: Optional[Any] = None
) -> ForecastResult:
    hist = np.array(historical_daily_m, dtype=np.float64)
    if len(hist) < 3:
        hist = np.array([1.0, 1.05, 1.02, 1.08, 1.12], dtype=np.float64)
        
    hist_clean = np.maximum(1e-4, hist)
    log_hist = np.log(hist_clean)
    diffs = np.diff(log_hist)
    mean_drift = float(np.mean(diffs)) if len(diffs) > 0 else 0.001
    std_drift = float(np.std(diffs, ddof=1)) if len(diffs) > 1 else 0.02
    
    last_val = hist_clean[-1]
    
    event_multipliers = np.ones(horizon_days, dtype=np.float64)
    for ev in plan_events:
        start_day = max(0, min(horizon_days - 1, ev.effective_day_offset))
        eff_mult = 1.0 + ev.confidence * (ev.demand_multiplier - 1.0)
        event_multipliers[start_day:] *= eff_mult
        
    if random_draws is not None and hasattr(random_draws, "get_demand_draws"):
        z = random_draws.get_demand_draws(num_scenarios, horizon_days)
    else:
        rng = np.random.default_rng(random_seed)
        z = rng.standard_normal(size=(num_scenarios, horizon_days))
    daily_increments = mean_drift + (std_drift * z)
    
    cum_increments = np.cumsum(daily_increments, axis=1)
    base_trajectories = last_val * np.exp(cum_increments)
    
    simulated_paths = base_trajectories * event_multipliers[np.newaxis, :]
    
    days_grid = list(range(1, horizon_days + 1))
    p10_daily = [round(float(np.percentile(simulated_paths[:, d], 10)), 3) for d in range(horizon_days)]
    p50_daily = [round(float(np.percentile(simulated_paths[:, d], 50)), 3) for d in range(horizon_days)]
    p90_daily = [round(float(np.percentile(simulated_paths[:, d], 90)), 3) for d in range(horizon_days)]
    
    total_demands = np.sum(simulated_paths, axis=1)
    
    return ForecastResult(
        horizon_days=horizon_days,
        days_grid=days_grid,
        p10_daily_m=p10_daily,
        median_daily_m=p50_daily,
        p90_daily_m=p90_daily,
        expected_total_demand_m=round(float(np.mean(total_demands)), 2),
        p10_total_demand_m=round(float(np.percentile(total_demands, 10)), 2),
        p50_total_demand_m=round(float(np.percentile(total_demands, 50)), 2),
        p90_total_demand_m=round(float(np.percentile(total_demands, 90)), 2),
        scenario_total_demands=total_demands
    )
