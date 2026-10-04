import math
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from scipy import stats

def simulate_jump_diffusion_paths(
    spot_initial: float,
    drift: float,
    volatility: float,
    hazard_rate: float,
    jump_mean: float,
    tenor_days: int = 90,
    num_paths: int = 5000,
    seed: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    time_years = tenor_days / 365.0
    dt = time_years / tenor_days
    
    z = rng.standard_normal(size=(num_paths, tenor_days))
    arrivals = rng.poisson(lam=hazard_rate * dt, size=(num_paths, tenor_days))
    
    drift_step = (drift - 0.5 * (volatility ** 2)) * dt
    diffusion_step = volatility * math.sqrt(dt) * z
    jump_penalty = math.log(max(1e-4, 1.0 - jump_mean))
    jump_step = arrivals * jump_penalty
    
    increments = drift_step + diffusion_step + jump_step
    log_paths = np.empty((num_paths, tenor_days + 1), dtype=np.float64)
    log_paths[:, 0] = math.log(spot_initial)
    log_paths[:, 1:] = math.log(spot_initial) + np.cumsum(increments, axis=1)
    
    paths = np.exp(log_paths)
    terminal_prices = paths[:, -1]
    has_jump = np.any(arrivals > 0, axis=1)
    return (paths, terminal_prices, has_jump)

def compute_forecast_cone(
    paths: np.ndarray,
    lower_pct: float = 5.0,
    upper_pct: float = 95.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    lower_bound = np.percentile(paths, lower_pct, axis=0)
    upper_bound = np.percentile(paths, upper_pct, axis=0)
    median_path = np.median(paths, axis=0)
    return (lower_bound, median_path, upper_bound)

def compute_obsolescence_premium(
    spot_initial: float,
    drift: float,
    volatility: float,
    hazard_rates: List[float],
    jump_mean: float,
    tenor_days: int = 90
) -> List[float]:
    t_years = tenor_days / 365.0
    premiums = []
    base_f0 = spot_initial * math.exp(drift * t_years)

    for lam in hazard_rates:
        fair_fwd = spot_initial * math.exp((drift - (lam * jump_mean)) * t_years)
        premium = base_f0 - fair_fwd
        premiums.append(float(premium))
    return premiums

def check_obsolescence_premium_monotonicity(premiums: List[float]) -> bool:
    if len(premiums) < 2:
        return True
    return all(premiums[i] < premiums[i+1] for i in range(len(premiums) - 1))
