import numpy as np
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from stampede.types import Quantity, Provenance, Notice, StandingNotices

class ExitRouteDistribution(BaseModel):
    mechanism: str
    p10_recovery_usd: Quantity
    p50_recovery_usd: Quantity
    p90_recovery_usd: Quantity
    expected_recovery_pct: Quantity

class ExitRouteReport(BaseModel):
    sell_day: int
    remaining_share: float
    depth: str
    substitutability_feasible: bool = True
    same_model: ExitRouteDistribution
    substitution_aware: ExitRouteDistribution
    secondary_spread_recovery_lift_usd: Quantity
    notices: List[Notice]

    @property
    def recovery_same_model(self) -> Quantity:
        return self.same_model.p50_recovery_usd

    @property
    def recovery_substitute(self) -> Quantity:
        return self.substitution_aware.p50_recovery_usd

def evaluate_exit_recovery(
    contract_notional_m: float = 50.0,
    unit_strike_usd: float = 4.00,
    tenor_days: int = 90,
    sell_day: int = 30,
    remaining_share: float = 0.67,
    depth: str = "normal",
    successor_launch_day: Optional[int] = None,
    price_cut_pct: float = 0.0,
    substitutability_feasible: bool = True,
    n_draws: int = 100,
    seed: int = 42
) -> ExitRouteReport:
    rng = np.random.default_rng(seed)
    remaining_value = contract_notional_m * unit_strike_usd * remaining_share

    depth_mult = 1.0 if depth == "normal" else (0.75 if depth == "thin" else 1.25)
    time_decay = max(0.1, (tenor_days - sell_day) / tenor_days)

    cut_impact = 1.0 - (price_cut_pct / 100.0)
    if successor_launch_day and sell_day >= successor_launch_day:
        cut_impact *= 0.70

    base_pct_same = 0.35 * depth_mult * time_decay * cut_impact
    base_pct_sub = 0.52 * depth_mult * time_decay * cut_impact

    same_draws = []
    sub_draws = []
    diff_draws = []

    for _ in range(n_draws):
        shock_same = rng.uniform(0.70, 1.30)
        draw_pct_same = min(1.0, max(0.05, base_pct_same * shock_same))
        r_same = remaining_value * draw_pct_same

        if substitutability_feasible:
            lift_factor = rng.uniform(0.10, 0.25) * depth_mult * time_decay * cut_impact
            draw_pct_sub = min(1.0, draw_pct_same + lift_factor)
            r_sub = remaining_value * draw_pct_sub
        else:
            draw_pct_sub = draw_pct_same
            r_sub = r_same

        same_draws.append(r_same)
        sub_draws.append(r_sub)
        diff_draws.append(r_sub - r_same)

    same_arr = np.array(same_draws)
    sub_arr = np.array(sub_draws)
    diff_arr = np.array(diff_draws)

    same_p10 = float(np.percentile(same_arr, 10.0))
    same_p50 = float(np.percentile(same_arr, 50.0))
    same_p90 = float(np.percentile(same_arr, 90.0))

    sub_p10 = float(np.percentile(sub_arr, 10.0))
    sub_p50 = float(np.percentile(sub_arr, 50.0))
    sub_p90 = float(np.percentile(sub_arr, 90.0))

    spread_lift = float(np.median(diff_arr)) if substitutability_feasible else 0.0

    if substitutability_feasible and len(diff_arr) > 0:
        boot_diffs = [float(np.mean(rng.choice(diff_arr, size=len(diff_arr), replace=True))) for _ in range(1000)]
        diff_lo90 = float(np.percentile(boot_diffs, 5.0))
        diff_hi90 = float(np.percentile(boot_diffs, 95.0))
    else:
        diff_lo90 = 0.0
        diff_hi90 = 0.0

    return ExitRouteReport(
        sell_day=sell_day,
        remaining_share=remaining_share,
        depth=depth,
        substitutability_feasible=substitutability_feasible,
        same_model=ExitRouteDistribution(
            mechanism="same_model_only",
            p10_recovery_usd=Quantity(
                id="exit.same_model.p10",
                value=round(same_p10, 2),
                unit="usd",
                provenance=Provenance.SIMULATED,
                source="secondary_market_model"
            ),
            p50_recovery_usd=Quantity(
                id="exit.same_model.p50",
                value=round(same_p50, 2),
                unit="usd",
                provenance=Provenance.SIMULATED,
                source="secondary_market_model"
            ),
            p90_recovery_usd=Quantity(
                id="exit.same_model.p90",
                value=round(same_p90, 2),
                unit="usd",
                provenance=Provenance.SIMULATED,
                source="secondary_market_model"
            ),
            expected_recovery_pct=Quantity(
                id="exit.same_model.pct",
                value=round(base_pct_same * 100.0, 2),
                unit="percent",
                provenance=Provenance.SIMULATED,
                source="secondary_market_model"
            )
        ),
        substitution_aware=ExitRouteDistribution(
            mechanism="substitution_aware",
            p10_recovery_usd=Quantity(
                id="exit.substitution_aware.p10",
                value=round(sub_p10, 2),
                unit="usd",
                provenance=Provenance.SIMULATED,
                source="secondary_market_model"
            ),
            p50_recovery_usd=Quantity(
                id="exit.substitution_aware.p50",
                value=round(sub_p50, 2),
                unit="usd",
                provenance=Provenance.SIMULATED,
                source="secondary_market_model"
            ),
            p90_recovery_usd=Quantity(
                id="exit.substitution_aware.p90",
                value=round(sub_p90, 2),
                unit="usd",
                provenance=Provenance.SIMULATED,
                source="secondary_market_model"
            ),
            expected_recovery_pct=Quantity(
                id="exit.substitution_aware.pct",
                value=round(base_pct_sub * 100.0, 2),
                unit="percent",
                provenance=Provenance.SIMULATED,
                source="secondary_market_model"
            )
        ),
        secondary_spread_recovery_lift_usd=Quantity(
            id="exit.recovery_spread_lift_usd",
            value=round(spread_lift, 2),
            lo90=round(diff_lo90, 2),
            hi90=round(diff_hi90, 2),
            n=n_draws,
            unit="usd",
            provenance=Provenance.SIMULATED,
            source="secondary_clearing_spread"
        ),
        notices=[StandingNotices.SIMULATED_EXIT_POOL]
    )

def simulate_exit_recovery(
    spot_at_sale: float = 4.20,
    strike: float = 3.50,
    remaining_days: int = 45,
    tenor_days: int = 90,
    substitute_penalty: float = 0.15,
    substitutability_feasible: bool = True
) -> ExitRouteReport:
    return evaluate_exit_recovery(
        contract_notional_m=50.0,
        unit_strike_usd=strike,
        tenor_days=tenor_days,
        sell_day=max(0, tenor_days - remaining_days),
        substitutability_feasible=substitutability_feasible
    )
