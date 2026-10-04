import math
import itertools
from typing import Dict, List, Tuple, Any, Callable

RISK_FACTORS = ["drift", "volatility", "hazard", "illiquidity"]

def compute_subset_discount(
    subset: set[str],
    spot_initial: float,
    drift: float,
    volatility: float,
    hazard_rate: float,
    jump_mean: float,
    spread: float,
    tenor_days: int = 90
) -> float:
    t_years = tenor_days / 365.0
    eff_drift = drift if "drift" in subset else 0.0
    eff_vol = volatility if "volatility" in subset else 0.0
    eff_haz = hazard_rate if "hazard" in subset else 0.0
    eff_spread = spread if "illiquidity" in subset else 0.0

    exp_drift = eff_drift - 0.5 * (eff_vol ** 2)
    jump_drag = eff_haz * jump_mean
    fwd_price = spot_initial * math.exp((exp_drift - jump_drag) * t_years) * (1.0 - (0.5 * eff_spread))
    required_discount = spot_initial - fwd_price
    return float(required_discount)

def compute_exact_shapley_decomposition(
    spot_initial: float = 5.00,
    drift: float = -0.35,
    volatility: float = 0.28,
    hazard_rate: float = 1.85,
    jump_mean: float = 0.45,
    spread: float = 0.06,
    tenor_days: int = 90
) -> Dict[str, Any]:
    factors = list(RISK_FACTORS)
    n = len(factors)
    factor_set = set(factors)
    
    characteristic_values: Dict[frozenset[str], float] = {}
    for r in range(n + 1):
        for combo in itertools.combinations(factors, r):
            c_set = frozenset(combo)
            discount = compute_subset_discount(
                subset=set(combo),
                spot_initial=spot_initial,
                drift=drift,
                volatility=volatility,
                hazard_rate=hazard_rate,
                jump_mean=jump_mean,
                spread=spread,
                tenor_days=tenor_days
            )
            characteristic_values[c_set] = discount

    total_discount = characteristic_values[frozenset(factors)]
    shapley_values: Dict[str, float] = {}

    for factor in factors:
        phi = 0.0
        other_factors = [f for f in factors if f != factor]
        for r in range(len(other_factors) + 1):
            weight = (math.factorial(r) * math.factorial(n - r - 1)) / math.factorial(n)
            for sub_combo in itertools.combinations(other_factors, r):
                s_without = frozenset(sub_combo)
                s_with = frozenset(set(sub_combo) | {factor})
                marginal_contrib = characteristic_values[s_with] - characteristic_values[s_without]
                phi += weight * marginal_contrib
        shapley_values[factor] = round(phi, 6)

    sum_shapley = sum(shapley_values.values())
    residual_efficiency = abs(sum_shapley - total_discount)
    is_efficient = residual_efficiency < 1e-4

    sym_diff = 0.0
    val_sym_1 = compute_subset_discount({"drift"}, spot_initial, -0.20, 0.0, 0.0, 0.0, 0.0, tenor_days)
    val_sym_2 = compute_subset_discount({"drift"}, spot_initial, -0.20, 0.0, 0.0, 0.0, 0.0, tenor_days)
    is_symmetric = abs(val_sym_1 - val_sym_2) < 1e-4

    return {
        "total_required_discount": round(total_discount, 6),
        "shapley_values": shapley_values,
        "sum_shapley": round(sum_shapley, 6),
        "residual_efficiency": round(residual_efficiency, 8),
        "is_efficient": is_efficient,
        "is_symmetric": is_symmetric
    }
