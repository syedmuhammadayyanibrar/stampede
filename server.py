import os
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from copilot.parser import parse_usage_csv
from copilot.plans import extract_demand_plans
from copilot.forecast import generate_demand_forecast
from copilot.sizing import compute_optimal_contract_order
from copilot.fit_check import evaluate_prompt_fit
from copilot.explain import generate_copilot_explanation
from migration import get_empirical_migration_dataset
from crunch_experiment import run_data_driven_crunch_comparison
from stampede.api.routes import router as stampede_router
from stampede.settings import settings
from stampede.costs import global_cost_ledger
from stampede.stages.seller_view import compute_seller_uplift

app = FastAPI(title="Stampede Risk Engine & Contract API")
app.include_router(stampede_router, prefix="/api/v1")

class ParseRequest(BaseModel):
    csv_content: str

class FitCheckRequest(BaseModel):
    prompts: List[str]
    spot_price_frontier: float = 5.00
    spot_price_discounted: float = 3.63

class CopilotRunRequest(BaseModel):
    csv_content: str
    plan_text: str = ""
    spot_price_frontier: float = 5.00
    spot_price_discounted: float = 3.63
    horizon_days: int = 90
    num_scenarios: int = 3000
    prompts: Optional[List[str]] = None

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "touchmark-risk-engine"}

@app.get("/budget")
def root_budget():
    return {
        "session_cap_usd": settings.session_cap_usd,
        "daily_cap_usd": settings.daily_cap_usd,
        "global_daily_spend_usd": global_cost_ledger.get_daily_spend(),
        "kill_switch_active": settings.kill_switch_active
    }

@app.post("/seller/uplift")
def root_seller_uplift(body: Optional[dict] = Body(default=None)):
    body = body or {}
    report = compute_seller_uplift(
        capacity_params=body.get("capacity_params"),
        demand_params=body.get("demand_params"),
        committed_share=body.get("committed_share", 0.70),
        forecast_error=body.get("forecast_error", 0.20)
    )
    return report.model_dump()

@app.get("/api/data")
def get_site_data():
    path = os.path.join("web", "data.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Site data not generated yet")
    with open(path, "r", encoding="utf-8") as f:
        return JSONResponse(content=json.load(f))

@app.post("/api/copilot/parse")
def api_parse_csv(req: ParseRequest):
    res = parse_usage_csv(req.csv_content)
    if not res.success:
        raise HTTPException(status_code=400, detail=res.error or "Failed to parse CSV")
    return {
        "success": True,
        "num_days": res.num_days,
        "total_tokens_m": round(res.total_tokens_millions, 2),
        "mean_daily_tokens_m": round(res.mean_daily_tokens_millions, 2),
        "daily_volatility": round(res.std_daily_tokens_millions, 4),
        "detected_model": res.detected_model,
        "daily_tokens": res.daily_tokens_millions
    }

@app.post("/api/copilot/fit-check")
def api_fit_check(req: FitCheckRequest):
    res = evaluate_prompt_fit(
        req.prompts,
        frontier_cost_per_m=req.spot_price_frontier,
        cheaper_cost_per_m=req.spot_price_discounted
    )
    return {
        "total_prompts": res.total_prompts,
        "sufficient_count": res.sufficient_count,
        "sufficiency_rate_pct": round(res.sufficiency_rate_pct, 1),
        "ci_lower_pct": round(res.wilson_ci[0], 1),
        "ci_upper_pct": round(res.wilson_ci[1], 1),
        "dollar_savings_per_m": round(res.dollar_savings_per_m, 2),
        "evaluations": [
            {
                "prompt": item["prompt_snippet"],
                "suitable": item["sufficient"],
                "quality_score": item["quality_score"],
                "rationale": item["rationale"]
            }
            for item in res.detailed_scores
        ]
    }

@app.post("/api/copilot/run")
def api_copilot_run(req: CopilotRunRequest):
    parsed = parse_usage_csv(req.csv_content)
    if not parsed.success:
        raise HTTPException(status_code=400, detail=parsed.error or "Failed to parse CSV")
        
    plans = extract_demand_plans(req.plan_text)
    
    forecast = generate_demand_forecast(
        parsed.daily_tokens_millions,
        plans,
        horizon_days=req.horizon_days,
        num_scenarios=req.num_scenarios,
        random_seed=42
    )
    
    rec = compute_optimal_contract_order(
        forecast,
        spot_initial=req.spot_price_frontier,
        fair_fwd_price=req.spot_price_discounted,
        crunch_spread_pct=0.358
    )
    
    prompts_to_eval = req.prompts or [
        "Summarize daily engineering ticket activity",
        "Extract structured billing invoice details from PDF",
        "Classify user chat intent across customer categories"
    ]
    
    fit_res = evaluate_prompt_fit(
        prompts_to_eval,
        frontier_cost_per_m=req.spot_price_frontier,
        cheaper_cost_per_m=req.spot_price_discounted
    )
    
    explanation = generate_copilot_explanation(rec, parsed, forecast)
    
    step = 3
    days_sampled = list(range(0, forecast.horizon_days, step))
    if days_sampled[-1] != forecast.horizon_days - 1:
        days_sampled.append(forecast.horizon_days - 1)
        
    return {
        "parsed": {
            "num_days": parsed.num_days,
            "total_tokens_m": round(parsed.total_tokens_millions, 2),
            "mean_daily_tokens_m": round(parsed.mean_daily_tokens_millions, 2),
            "daily_volatility": round(parsed.std_daily_tokens_millions, 4),
            "detected_model": parsed.detected_model
        },
        "plans": [
            {
                "description": ev.description,
                "multiplier": ev.demand_multiplier,
                "confidence": ev.confidence,
                "quote": ev.source_quote
            }
            for ev in plans
        ],
        "forecast": {
            "expected_total_m": round(forecast.expected_total_demand_m, 2),
            "p10_total_m": round(forecast.p10_total_demand_m, 2),
            "p90_total_m": round(forecast.p90_total_demand_m, 2),
            "days": days_sampled,
            "p10_daily": [round(forecast.p10_daily_m[i], 2) for i in days_sampled],
            "median_daily": [round(forecast.median_daily_m[i], 2) for i in days_sampled],
            "p90_daily": [round(forecast.p90_daily_m[i], 2) for i in days_sampled]
        },
        "recommendation": {
            "optimal_notional_m": round(rec.optimal_notional_m, 1),
            "naive_notional_m": round(rec.naive_notional_m, 1),
            "critical_ratio": round(rec.critical_ratio, 3),
            "forward_strike_per_m": round(rec.forward_strike_per_m, 2),
            "expected_fwd_bill": round(rec.expected_fwd_bill, 0),
            "expected_spot_bill": round(rec.expected_spot_bill, 0),
            "expected_savings": round(rec.expected_savings, 0),
            "savings_pct": round(rec.savings_pct, 1),
            "downside_p95_cost": round(rec.downside_p95_cost, 0),
            "crunch_exposure_penalty": round(rec.crunch_exposure_penalty, 0),
            "portfolio_mix": rec.portfolio_mix
        },
        "fit_check": {
            "total_prompts": fit_res.total_prompts,
            "sufficient_count": fit_res.sufficient_count,
            "sufficiency_rate_pct": round(fit_res.sufficiency_rate_pct, 1),
            "ci_lower_pct": round(fit_res.wilson_ci[0], 1),
            "ci_upper_pct": round(fit_res.wilson_ci[1], 1),
            "dollar_savings_per_m": round(fit_res.dollar_savings_per_m, 2),
            "evaluations": [
                {
                    "prompt": item["prompt_snippet"],
                    "suitable": item["sufficient"],
                    "quality_score": item["quality_score"],
                    "rationale": item["rationale"]
                }
                for item in fit_res.detailed_scores
            ]
        },
        "explanation": explanation
    }

@app.get("/api/migration/dataset")
def api_migration():
    return get_empirical_migration_dataset()

@app.get("/api/crunch/data-driven")
def api_crunch_comparison():
    return run_data_driven_crunch_comparison()

app.mount("/", StaticFiles(directory="web", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)
