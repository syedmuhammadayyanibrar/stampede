from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import numpy as np
from copilot.plans import extract_demand_plans, PlanEvent
from copilot.forecast import generate_demand_forecast, ForecastResult
from stampede.types import Quantity, Series, Provenance

class ForecastReport(BaseModel):
    horizon_days: int
    p10_daily: Series
    p50_daily: Series
    p90_daily: Series
    expected_total_m: Quantity
    p10_total_m: Quantity
    p50_total_m: Quantity
    p90_total_m: Quantity
    extracted_events: List[Dict[str, Any]] = []
    scenario_total_demands: List[float]

    @property
    def total_tokens_q50(self) -> float:
        return self.p50_total_m.value

    @property
    def mean_daily_tokens(self) -> float:
        return self.expected_total_m.value / max(1, self.horizon_days)

    @property
    def std_daily_tokens(self) -> float:
        if self.scenario_total_demands:
            return float(np.std(self.scenario_total_demands) / max(1, self.horizon_days))
        return 0.0

UsageForecastResult = ForecastReport

def run_forecast_stage(
    daily_history_m: List[float],
    notes: str = "",
    horizon_days: int = 90,
    num_scenarios: int = 4000,
    random_draws: Optional[Any] = None,
    seed: int = 42
) -> ForecastReport:
    plan_events = extract_demand_plans(notes)

    f_res = generate_demand_forecast(
        historical_daily_m=daily_history_m,
        plan_events=plan_events,
        horizon_days=horizon_days,
        num_scenarios=num_scenarios,
        random_seed=seed,
        random_draws=random_draws
    )

    ev_dicts = [
        {
            "event_type": ev.event_type,
            "demand_multiplier": ev.demand_multiplier,
            "confidence": ev.confidence,
            "effective_day_offset": ev.effective_day_offset,
            "evidence_quote": ev.evidence_quote
        }
        for ev in plan_events
    ]

    scenario_totals = [round(float(v), 4) for v in f_res.scenario_total_demands]

    return ForecastReport(
        horizon_days=horizon_days,
        p10_daily=Series(
            name="forecast_p10_daily",
            unit="millions_tokens_per_day",
            provenance=Provenance.SIMULATED,
            source="monte_carlo_forecast",
            values=f_res.p10_daily_m
        ),
        p50_daily=Series(
            name="forecast_p50_daily",
            unit="millions_tokens_per_day",
            provenance=Provenance.SIMULATED,
            source="monte_carlo_forecast",
            values=f_res.median_daily_m
        ),
        p90_daily=Series(
            name="forecast_p90_daily",
            unit="millions_tokens_per_day",
            provenance=Provenance.SIMULATED,
            source="monte_carlo_forecast",
            values=f_res.p90_daily_m
        ),
        expected_total_m=Quantity(
            id="forecast.expected_total_m",
            value=round(f_res.expected_total_demand_m, 4),
            unit="millions_tokens",
            provenance=Provenance.SIMULATED,
            source="monte_carlo_forecast"
        ),
        p10_total_m=Quantity(
            id="forecast.p10_total_m",
            value=round(f_res.p10_total_demand_m, 4),
            unit="millions_tokens",
            provenance=Provenance.SIMULATED,
            source="monte_carlo_forecast"
        ),
        p50_total_m=Quantity(
            id="forecast.p50_total_m",
            value=round(f_res.p50_total_demand_m, 4),
            unit="millions_tokens",
            provenance=Provenance.SIMULATED,
            source="monte_carlo_forecast"
        ),
        p90_total_m=Quantity(
            id="forecast.p90_total_m",
            value=round(f_res.p90_total_demand_m, 4),
            unit="millions_tokens",
            provenance=Provenance.SIMULATED,
            source="monte_carlo_forecast"
        ),
        extracted_events=ev_dicts,
        scenario_total_demands=scenario_totals
    )

def run_forecast_monte_carlo(
    history_tokens: List[float],
    days_ahead: int = 90,
    random_draws: Optional[Any] = None,
    seed: int = 42
) -> ForecastReport:
    return run_forecast_stage(
        daily_history_m=history_tokens,
        horizon_days=days_ahead,
        random_draws=random_draws,
        seed=seed
    )
