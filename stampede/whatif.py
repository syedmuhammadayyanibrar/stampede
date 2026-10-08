import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from stampede.stages.forecast import run_forecast_monte_carlo, UsageForecastResult
from stampede.stages.sizing_live import calculate_live_sizing, LiveSizingResult
from stampede.stages.valuation_live import run_live_valuation, LiveValuationResult
from stampede.stages.quotes_rank import rank_quotes_risk_adjusted, RankedQuote
from stampede.stages.planner import solve_plan, PlanResult
from stampede.explain import generate_shapley_explanation, ExplainReport

class WhatIfResult(BaseModel):
    recompute_ms: float
    touched_stages: List[str]
    forecast: Optional[Dict[str, Any]] = None
    sizing: Optional[Dict[str, Any]] = None
    valuation: Optional[Dict[str, Any]] = None
    quotes_ranked: Optional[List[Dict[str, Any]]] = None
    plan: Optional[Dict[str, Any]] = None
    explanation: Optional[Dict[str, Any]] = None
    reservation_prices: Optional[List[Dict[str, Any]]] = None
    overrides_applied: Dict[str, Any]

def execute_whatif_recompute(
    base_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> WhatIfResult:
    start_time = time.perf_counter()
    if not overrides:
        elapsed = (time.perf_counter() - start_time) * 1000.0
        return WhatIfResult(
            recompute_ms=round(elapsed, 2),
            touched_stages=[],
            forecast=base_state.get("forecast"),
            sizing=base_state.get("sizing"),
            valuation=base_state.get("valuation"),
            quotes_ranked=base_state.get("quotes_ranked"),
            plan=base_state.get("plan"),
            explanation=base_state.get("explanation"),
            overrides_applied={}
        )

    touched: List[str] = []
    current_forecast = base_state.get("forecast", {})
    current_sizing = base_state.get("sizing", {})
    current_valuation = base_state.get("valuation", {})
    current_quotes_ranked = base_state.get("quotes_ranked", [])
    current_plan = base_state.get("plan", {})
    current_explain = base_state.get("explanation", {})

    random_draws = base_state.get("random_draws")
    base_history = base_state.get("history_tokens", [1000000.0] * 30)

    if "growth_multiplier" in overrides:
        touched.append("forecast")
        mult = float(overrides["growth_multiplier"])
        scaled_history = [v * mult for v in base_history]
        fc_res = run_forecast_monte_carlo(scaled_history, days_ahead=90, random_draws=random_draws)
        current_forecast = fc_res.model_dump()

    if "growth_multiplier" in overrides or "risk_aversion" in overrides:
        touched.append("sizing")
        q_mean = current_forecast.get("mean_daily_tokens", 1000000.0) if isinstance(current_forecast, dict) else 1000000.0
        q_std = current_forecast.get("std_daily_tokens", 150000.0) if isinstance(current_forecast, dict) else 150000.0
        sz_res = calculate_live_sizing(
            mean_demand=float(q_mean),
            sd_demand=float(q_std),
            on_demand_rate=5.00,
            committed_rate=3.50,
            salvage_rate=1.50
        )
        current_sizing = sz_res.model_dump()

    if any(k in overrides for k in ["price_cut", "depth", "successor_launch_day"]):
        touched.append("valuation")
        p_cut = float(overrides.get("price_cut", 0.40))
        val_res = run_live_valuation(
            spot_initial=5.00,
            prepay_share=0.20,
            tenor_days=90,
            cost_of_capital=0.10,
            random_draws=random_draws
        )
        current_valuation = val_res.model_dump()

    if any(k in overrides for k in ["price_cut", "depth", "successor_launch_day", "risk_aversion"]):
        touched.append("quotes_rank")
        raw_quotes = base_state.get("raw_quotes", [])
        if raw_quotes:
            rho_val = float(overrides.get("risk_aversion", 0.50))
            q_ranked_objs = rank_quotes_risk_adjusted(raw_quotes, rho=rho_val)
            current_quotes_ranked = [q.model_dump() for q in q_ranked_objs]

    if touched or any(k in overrides for k in ["excluded_providers", "risk_aversion"]):
        touched.append("planner")
        q_star_val = current_sizing.get("optimal_sizing_tokens", {}).get("value", 1000000.0) if isinstance(current_sizing, dict) else 1000000.0
        base_spend = base_state.get("baseline_spend_usd", 15000.0)
        rho_val = float(overrides.get("risk_aversion", 0.50))
        plan_res = solve_plan(
            quotes_ranked=current_quotes_ranked,
            q_star=float(q_star_val),
            baseline_spend=float(base_spend),
            rho=rho_val
        )
        current_plan = plan_res.model_dump()

    current_res_prices = base_state.get("reservation_prices")
    if random_draws is not None or "risk_aversion" in overrides:
        rho_val = float(overrides.get("risk_aversion", 0.50))
        from stampede.stages.valuation_live import compute_reservation_prices_table
        table = compute_reservation_prices_table(rho=rho_val, random_draws=random_draws)
        current_res_prices = [r.model_dump() for r in table]
        touched.append("reservation_prices")

    elapsed = (time.perf_counter() - start_time) * 1000.0

    return WhatIfResult(
        recompute_ms=round(elapsed, 2),
        touched_stages=touched,
        forecast=current_forecast,
        sizing=current_sizing,
        valuation=current_valuation,
        quotes_ranked=current_quotes_ranked,
        plan=current_plan,
        explanation=current_explain,
        reservation_prices=current_res_prices,
        overrides_applied=overrides
    )
