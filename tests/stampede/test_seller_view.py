from stampede.stages.seller_view import compute_seller_uplift
from stampede.types import Provenance, StandingNotices

def test_seller_view_simulation_and_notices():
    rep = compute_seller_uplift(
        capacity_params={"total_capacity_m": 600.0},
        demand_params={"mean_demand_m": 450.0},
        committed_share=0.75,
        forecast_error=0.15,
        seed=42
    )

    assert rep.uplift_p10_pct.provenance == Provenance.SIMULATED
    assert rep.uplift_median_pct.provenance == Provenance.SIMULATED
    assert rep.uplift_p90_pct.provenance == Provenance.SIMULATED
    assert rep.prob_positive_uplift.provenance == Provenance.SIMULATED
    assert rep.breakeven_forecast_error_pct.provenance == Provenance.SIMULATED

    assert rep.uplift_p90_pct.value >= rep.uplift_median_pct.value >= rep.uplift_p10_pct.value
    assert 0.0 <= rep.prob_positive_uplift.value <= 1.0
    assert StandingNotices.ASSUMED_SELLER_PARAMS in rep.notices
