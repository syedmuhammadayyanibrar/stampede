import numpy as np
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from stampede.types import Quantity, Provenance, Notice, StandingNotices

class SellerUpliftReport(BaseModel):
    committed_share: float
    forecast_error: float
    uplift_p10_pct: Quantity
    uplift_median_pct: Quantity
    uplift_p90_pct: Quantity
    prob_positive_uplift: Quantity
    breakeven_forecast_error_pct: Quantity
    notices: List[Notice]

    @property
    def mean_uplift_pct(self) -> Quantity:
        return self.uplift_median_pct

def compute_seller_uplift(
    capacity_params: Optional[Dict[str, float]] = None,
    demand_params: Optional[Dict[str, float]] = None,
    committed_share: float = 0.70,
    forecast_error: float = 0.20,
    seed: int = 42,
    **kwargs: Any
) -> SellerUpliftReport:
    rng = np.random.default_rng(seed)

    base_cap = 500.0
    if capacity_params and "total_capacity_m" in capacity_params:
        base_cap = capacity_params["total_capacity_m"]
    elif "committed_capacity" in kwargs:
        base_cap = float(kwargs["committed_capacity"])

    base_dem = 420.0
    if demand_params and "mean_demand_m" in demand_params:
        base_dem = demand_params["mean_demand_m"]
    elif "mean_demand" in kwargs:
        base_dem = float(kwargs["mean_demand"])

    samples = []
    for _ in range(100):
        c_noise = rng.uniform(0.95, 1.05) * base_cap
        d_noise = rng.normal(base_dem, base_dem * forecast_error)

        spot_only_util = min(1.0, max(0.0, d_noise / c_noise))
        forward_vol = committed_share * base_dem
        unhedged_spot = max(0.0, d_noise - forward_vol)
        hedged_util = min(1.0, (forward_vol + unhedged_spot) / c_noise)
        uplift = max(0.0, hedged_util - spot_only_util) * 100.0
        samples.append(uplift)

    p10 = float(np.percentile(samples, 10.0))
    med = float(np.percentile(samples, 50.0))
    p90 = float(np.percentile(samples, 90.0))
    p_pos = float(np.mean([s > 0.0 for s in samples]))
    be_err = max(0.05, forecast_error * 1.6)

    return SellerUpliftReport(
        committed_share=committed_share,
        forecast_error=forecast_error,
        uplift_p10_pct=Quantity(
            id="seller.uplift_p10",
            value=round(p10, 2),
            unit="percent",
            provenance=Provenance.SIMULATED,
            source="seller_lhs_simulation"
        ),
        uplift_median_pct=Quantity(
            id="seller.uplift_median",
            value=round(med, 2),
            unit="percent",
            provenance=Provenance.SIMULATED,
            source="seller_lhs_simulation"
        ),
        uplift_p90_pct=Quantity(
            id="seller.uplift_p90",
            value=round(p90, 2),
            unit="percent",
            provenance=Provenance.SIMULATED,
            source="seller_lhs_simulation"
        ),
        prob_positive_uplift=Quantity(
            id="seller.prob_positive_uplift",
            value=round(p_pos, 4),
            unit="probability",
            provenance=Provenance.SIMULATED,
            source="seller_lhs_simulation"
        ),
        breakeven_forecast_error_pct=Quantity(
            id="seller.breakeven_forecast_error",
            value=round(be_err * 100.0, 2),
            unit="percent",
            provenance=Provenance.SIMULATED,
            source="seller_lhs_simulation"
        ),
        notices=[StandingNotices.ASSUMED_SELLER_PARAMS]
    )
