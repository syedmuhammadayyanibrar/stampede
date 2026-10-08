import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel
from stampede.types import Quantity, Provenance

class SizingReport(BaseModel):
    optimal_notional_m: Quantity
    p90_peak_notional_m: Quantity
    v1_notional_m: Quantity
    critical_ratio: Quantity
    expected_salvage_usd: Quantity
    sizing_cost_advantage_vs_p90_pct: Quantity

def compute_newsvendor_sizing(
    scenario_demands: List[float],
    unit_strike_usd: float = 4.00,
    unit_on_demand_usd: float = 5.00,
    salvage_recovery_rate: float = 0.40
) -> SizingReport:
    arr = np.array(scenario_demands, dtype=np.float64)
    if len(arr) == 0:
        arr = np.array([40.0, 45.0, 50.0, 55.0, 60.0], dtype=np.float64)

    salvage_val = unit_strike_usd * salvage_recovery_rate
    co = max(0.01, unit_strike_usd - salvage_val)
    cu = max(0.01, unit_on_demand_usd - unit_strike_usd)
    cr = float(cu / (cu + co))
    cr_clamped = min(0.99, max(0.01, cr))

    q_opt = float(np.percentile(arr, cr_clamped * 100.0))
    q_p90 = float(np.percentile(arr, 90.0))
    q_v1 = float(np.median(arr))

    cost_opt = float(np.mean(np.maximum(0.0, arr - q_opt) * unit_on_demand_usd + q_opt * unit_strike_usd))
    cost_p90 = float(np.mean(np.maximum(0.0, arr - q_p90) * unit_on_demand_usd + q_p90 * unit_strike_usd))
    diff_pct = max(0.0, (cost_p90 - cost_opt) / max(1e-4, cost_p90)) * 100.0

    return SizingReport(
        optimal_notional_m=Quantity(
            id="sizing.optimal_notional_m",
            value=round(q_opt, 2),
            unit="millions_tokens",
            provenance=Provenance.SIMULATED,
            source="newsvendor_critical_ratio"
        ),
        p90_peak_notional_m=Quantity(
            id="sizing.p90_peak_notional_m",
            value=round(q_p90, 2),
            unit="millions_tokens",
            provenance=Provenance.SIMULATED,
            source="p90_peak_demand"
        ),
        v1_notional_m=Quantity(
            id="sizing.v1_notional_m",
            value=round(q_v1, 2),
            unit="millions_tokens",
            provenance=Provenance.SIMULATED,
            source="v1_median_sizing"
        ),
        critical_ratio=Quantity(
            id="sizing.critical_ratio",
            value=round(cr, 4),
            unit="ratio",
            provenance=Provenance.SIMULATED,
            source="underage_overage_ratio"
        ),
        expected_salvage_usd=Quantity(
            id="sizing.expected_salvage_usd",
            value=round(salvage_val, 4),
            unit="usd_per_m",
            provenance=Provenance.SIMULATED,
            source="exit_route_salvage"
        ),
        sizing_cost_advantage_vs_p90_pct=Quantity(
            id="sizing.cost_advantage_vs_p90_pct",
            value=round(diff_pct, 2),
            unit="percent",
            provenance=Provenance.SIMULATED,
            source="sizing_diagnostic_comparison",
            note="diagnostic_comparison"
        )
    )

class LiveSizingResult(BaseModel):
    optimal_sizing_tokens: Quantity
    critical_ratio: Quantity
    expected_savings: Quantity

def calculate_live_sizing(
    mean_demand: float,
    sd_demand: float,
    on_demand_rate: float = 5.0,
    committed_rate: float = 3.5,
    salvage_rate: float = 1.5
) -> LiveSizingResult:
    cu = max(0.01, on_demand_rate - committed_rate)
    co = max(0.01, committed_rate - salvage_rate)
    cr = float(cu / (cu + co))
    from scipy.stats import norm
    z = float(norm.ppf(min(0.99, max(0.01, cr))))
    q_opt = max(0.0, mean_demand + z * sd_demand)
    return LiveSizingResult(
        optimal_sizing_tokens=Quantity(id="sizing.q_star", value=round(q_opt, 2), provenance=Provenance.FITTED),
        critical_ratio=Quantity(id="sizing.critical_ratio", value=round(cr, 4), provenance=Provenance.FITTED),
        expected_savings=Quantity(id="sizing.expected_savings", value=round(q_opt * (on_demand_rate - committed_rate), 2), provenance=Provenance.FITTED)
    )
