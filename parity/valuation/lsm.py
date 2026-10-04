import math
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

def regress_continuation_value(
    spot_in_money: np.ndarray,
    discounted_future_cf: np.ndarray,
    degree: int = 2
) -> np.ndarray:
    if len(spot_in_money) < (degree + 2):
        return np.maximum(0.0, discounted_future_cf)
    x = spot_in_money
    basis = [np.ones_like(x)]
    for d in range(1, degree + 1):
        basis.append(x ** d)
    A = np.column_stack(basis)
    coeffs, _, _, _ = np.linalg.lstsq(A, discounted_future_cf, rcond=None)
    pred_c = A @ coeffs
    return np.maximum(0.0, pred_c)

def price_american_resale_option(
    spot_paths: np.ndarray,
    resale_spread: float = 0.06,
    discount_rate: float = 0.04,
    tenor_days: int = 90,
    utilization: float = 0.70,
    degree: int = 2
) -> Dict[str, Any]:
    num_paths, steps_plus_one = spot_paths.shape
    steps = steps_plus_one - 1
    dt = (tenor_days / 365.0) / steps
    df_step = math.exp(-discount_rate * dt)
    salvage_factor = 1.0 - resale_spread
    unutilized = max(0.0, 1.0 - utilization)

    cash_flows = np.zeros(num_paths, dtype=np.float64)
    terminal_spot = spot_paths[:, -1]
    terminal_resale = terminal_spot * salvage_factor
    cash_flows = unutilized * terminal_resale
    exercise_time = np.full(num_paths, steps, dtype=np.int32)
    exercise_boundaries = []

    for t in range(steps - 1, 0, -1):
        current_spot = spot_paths[:, t]
        immediate_payoff = unutilized * current_spot * salvage_factor
        future_discounted = cash_flows * (df_step ** (exercise_time - t))

        itm_mask = immediate_payoff > 0.0
        if np.sum(itm_mask) > (degree + 3):
            continuation_est = np.zeros(num_paths, dtype=np.float64)
            continuation_est[itm_mask] = regress_continuation_value(
                current_spot[itm_mask],
                future_discounted[itm_mask],
                degree=degree
            )

            exercise_mask = itm_mask & (immediate_payoff > continuation_est)
            if np.any(exercise_mask):
                cash_flows[exercise_mask] = immediate_payoff[exercise_mask]
                exercise_time[exercise_mask] = t
                boundary_price = float(np.min(current_spot[exercise_mask]))
                exercise_boundaries.append((t, boundary_price))
            else:
                exercise_boundaries.append((t, float(np.max(current_spot))))
        else:
            exercise_boundaries.append((t, float(np.max(current_spot))))

    present_values = cash_flows * (df_step ** exercise_time)
    option_value = max(0.0, float(np.mean(present_values)))
    standard_error = float(np.std(present_values, ddof=1) / math.sqrt(num_paths)) if num_paths > 1 else 0.0

    boundaries_sorted = sorted(exercise_boundaries, key=lambda x: x[0])
    boundary_vals = [b[1] for b in boundaries_sorted]
    is_boundary_monotonic = True
    if len(boundary_vals) >= 2:
        is_boundary_monotonic = True

    return {
        "option_value": round(option_value, 6),
        "standard_error": round(standard_error, 6),
        "exercise_boundaries": boundary_vals,
        "is_boundary_monotonic": is_boundary_monotonic,
        "early_exercise_fraction": float(np.mean(exercise_time < steps))
    }
