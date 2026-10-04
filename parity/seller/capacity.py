from dataclasses import dataclass
from typing import Dict, List, Any
import numpy as np

@dataclass(frozen=True)
class SellerCapacityProfile:
    seller_id: str
    model_name: str
    total_capacity_m: float
    baseline_utilization: float
    primary_price_per_m: float

def compute_effective_utilization(
    baseline_utilization: float,
    conversion_uptake: float,
    cannibalization_dampener: float = 0.80
) -> float:
    unutilized = max(0.0, 1.0 - baseline_utilization)
    gross_absorbed = unutilized * conversion_uptake
    net_absorbed = gross_absorbed * (1.0 - (1.0 - cannibalization_dampener) * 0.5)
    return min(1.0, baseline_utilization + net_absorbed)

def compute_secondary_spread(
    primary_price: float,
    effective_utilization: float,
    base_spread_factor: float = 0.35
) -> float:
    distress_ratio = max(0.01, 1.0 - effective_utilization)
    spread = primary_price * base_spread_factor * (distress_ratio / 0.35)
    return max(0.05, float(spread))

def evaluate_spread_compression(
    primary_price: float = 4.0,
    baseline_utilization: float = 0.65,
    cannibalization_dampener: float = 0.80,
    uptake_grid: List[float] = None
) -> Dict[str, Any]:
    if uptake_grid is None:
        uptake_grid = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    spreads = []
    utilizations = []

    for u in uptake_grid:
        eff_util = compute_effective_utilization(
            baseline_utilization=baseline_utilization,
            conversion_uptake=u,
            cannibalization_dampener=cannibalization_dampener
        )
        s = compute_secondary_spread(
            primary_price=primary_price,
            effective_utilization=eff_util
        )
        utilizations.append(round(eff_util, 4))
        spreads.append(round(s, 4))

    s0 = spreads[0]
    idx_50 = uptake_grid.index(0.5) if 0.5 in uptake_grid else 5
    s50 = spreads[idx_50]
    compression_ratio = max(0.0, (s0 - s50) / max(1e-6, s0))

    return {
        "uptake_grid": uptake_grid,
        "utilizations": utilizations,
        "spreads": spreads,
        "baseline_spread": s0,
        "spread_at_50pct": s50,
        "spread_compression_ratio": round(float(compression_ratio), 4),
        "baseline_utilization": baseline_utilization,
        "utilization_at_50pct": utilizations[idx_50]
    }
