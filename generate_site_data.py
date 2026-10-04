import json
import os
import numpy as np
from models import CALIBRATED_MODELS
from engine import run_monte_carlo
from crunch_experiment import run_liquidity_crunch_experiment, run_data_driven_crunch_comparison
from narrative_gen import generate_market_narrative
from migration import get_empirical_migration_dataset
from copilot.parser import parse_usage_csv
from copilot.plans import extract_demand_plans
from copilot.forecast import generate_demand_forecast
from copilot.sizing import compute_optimal_contract_order
from copilot.fit_check import evaluate_prompt_fit
from copilot.explain import generate_copilot_explanation

def main():
    os.makedirs("web", exist_ok=True)
    
    models_dict = {}
    for key, cal in CALIBRATED_MODELS.items():
        tenor_grid = [30, 60, 90, 180]
        fair_prices = {}
        for t in tenor_grid:
            sim_t = run_monte_carlo(cal, tenor_days=t, num_paths=12000, random_seed=42)
            fair_prices[str(t)] = round(sim_t.fair_forward_price, 3)
        
        sim_main = run_monte_carlo(cal, tenor_days=90, num_paths=8000, random_seed=42)
        paths = sim_main.spot_paths
        time_days = [int(round(t_yr * 365)) for t_yr in sim_main.time_grid]
        
        step_stride = 3
        sub_indices = list(range(0, len(time_days), step_stride))
        if sub_indices[-1] != len(time_days) - 1:
            sub_indices.append(len(time_days) - 1)
        
        days_sampled = [time_days[i] for i in sub_indices]
        p10 = [round(float(np.percentile(paths[:, i], 10)), 3) for i in sub_indices]
        p25 = [round(float(np.percentile(paths[:, i], 25)), 3) for i in sub_indices]
        median = [round(float(np.percentile(paths[:, i], 50)), 3) for i in sub_indices]
        p75 = [round(float(np.percentile(paths[:, i], 75)), 3) for i in sub_indices]
        p90 = [round(float(np.percentile(paths[:, i], 90)), 3) for i in sub_indices]
        
        sample_trajectories = []
        for p_idx in [0, 14, 28, 42, 56]:
            sample_trajectories.append([round(float(paths[p_idx, i]), 3) for i in sub_indices])
        
        models_dict[key] = {
            "provider": cal.provider,
            "family_name": cal.family_name,
            "spot_initial": cal.spot_price_initial,
            "annual_drift": cal.annual_drift,
            "annual_volatility": cal.annual_volatility,
            "hazard_rate": cal.hazard_rate_annual,
            "jump_mean": cal.jump_mean,
            "fair_prices_by_tenor": fair_prices,
            "fan_chart": {
                "days": days_sampled,
                "p10": p10,
                "p25": p25,
                "median": median,
                "p75": p75,
                "p90": p90,
                "sample_trajectories": sample_trajectories
            }
        }
    
    crunch_res = run_liquidity_crunch_experiment(
        calibration=CALIBRATED_MODELS["openai_gpt_tier"],
        tenor_days=90,
        advertised_discount_pct=0.15,
        num_paths=25000,
        resale_window_days=14,
        random_seed=42
    )
    
    narrative_input = {
        "lcr_benchmark": crunch_res.lcr_benchmark,
        "lcr_benchmark_ci_lower": crunch_res.lcr_benchmark_ci_lower,
        "lcr_benchmark_ci_upper": crunch_res.lcr_benchmark_ci_upper,
        "lcr_spread": crunch_res.lcr_spread,
        "lcr_spread_ci_lower": crunch_res.lcr_spread_ci_lower,
        "lcr_spread_ci_upper": crunch_res.lcr_spread_ci_upper,
        "resale_spread_normal": crunch_res.resale_spread_normal,
        "resale_spread_shock": crunch_res.resale_spread_shock,
        "fair_forward_price": crunch_res.fair_forward_price,
        "fair_cost_spot_shock": crunch_res.fair_cost_spot_shock,
        "fair_cost_fwd_actual_shock": crunch_res.fair_cost_fwd_actual_shock,
        "fair_total_shock_penalty": crunch_res.fair_total_shock_penalty,
        "fair_total_shock_penalty_pct": crunch_res.fair_total_shock_penalty_pct,
        "fair_liquidity_blowout_penalty": crunch_res.fair_liquidity_blowout_penalty,
        "naive_net_cost_penalty": crunch_res.naive_net_cost_penalty,
        "naive_net_cost_penalty_pct": crunch_res.naive_net_cost_penalty_pct
    }
    narrative = generate_market_narrative(narrative_input)
    
    headline_data = {
        "lcr_benchmark": round(crunch_res.lcr_benchmark, 2),
        "lcr_benchmark_ci": [round(crunch_res.lcr_benchmark_ci_lower, 2), round(crunch_res.lcr_benchmark_ci_upper, 2)],
        "lcr_spread": round(crunch_res.lcr_spread, 2),
        "lcr_spread_ci": [round(crunch_res.lcr_spread_ci_lower, 2), round(crunch_res.lcr_spread_ci_upper, 2)],
        "spread_normal_pct": round(crunch_res.resale_spread_normal * 100, 1),
        "spread_shock_pct": round(crunch_res.resale_spread_shock * 100, 1),
        "mean_resale_normal": round(crunch_res.mean_resale_normal, 2),
        "mean_resale_shock": round(crunch_res.mean_resale_shock, 2),
        "shock_probability_pct": round(crunch_res.shock_prob_empirical * 100, 1),
        "fair_forward_price": round(crunch_res.fair_forward_price, 2),
        "strike_price_naive": round(crunch_res.strike_price_naive, 2),
        "initial_spot": round(crunch_res.initial_spot, 2),
        "fair_cost_spot_shock": round(crunch_res.fair_cost_spot_shock, 3),
        "fair_cost_fwd_actual_shock": round(crunch_res.fair_cost_fwd_actual_shock, 3),
        "fair_total_shock_penalty": round(crunch_res.fair_total_shock_penalty, 3),
        "fair_total_shock_penalty_pct": round(crunch_res.fair_total_shock_penalty_pct, 1),
        "fair_liquidity_blowout_penalty": round(crunch_res.fair_liquidity_blowout_penalty, 3),
        "naive_cost_penalty": round(crunch_res.naive_net_cost_penalty, 3),
        "naive_cost_penalty_pct": round(crunch_res.naive_net_cost_penalty_pct, 1),
        "narrative": narrative,
        "comparison_bars": {
            "categories": ["Normal Idiosyncratic Resale", "Correlated Obsolescence Shock"],
            "resale_prices": [round(crunch_res.mean_resale_normal, 2), round(crunch_res.mean_resale_shock, 2)],
            "resale_spreads": [round(crunch_res.resale_spread_normal * 100, 1), round(crunch_res.resale_spread_shock * 100, 1)]
        },
        "stress_scenarios": [
            {
                "title": "Secondary Market Freeze",
                "condition": "Shock spread expands to 65.0%",
                "lcr": f"{crunch_res.stress_scenarios['secondary_market_freeze']['lcr_benchmark']:.2f}x",
                "cost_penalty": f"+${crunch_res.stress_scenarios['secondary_market_freeze']['shock_net_penalty']:.3f}/M",
                "impact": "Market makers withdraw bids completely during mass liquidations"
            },
            {
                "title": "Buyer Utilization Collapse",
                "condition": "Internal workload consumes only 20.0% of capacity",
                "lcr": "Demand Shock",
                "cost_penalty": f"+${crunch_res.stress_scenarios['buyer_utilization_collapse']['shock_penalty']:.3f}/M",
                "impact": "Buyer forced to dump 80% volume into secondary market"
            },
            {
                "title": "Frontier Release War",
                "condition": "Obsolescence hazard doubles to 3.70 releases/year",
                "lcr": "Elevated Freq",
                "cost_penalty": f"+${crunch_res.stress_scenarios['frontier_release_war']['shock_penalty']:.3f}/M",
                "impact": "Rapid model iteration accelerates obsolescence shocks"
            }
        ]
    }
    
    crunch_comparison = run_data_driven_crunch_comparison()
    empirical_migration = get_empirical_migration_dataset()
    
    copilot_presets = {}
    preset_configs = [
        {
            "id": "openai_tier",
            "name": "OpenAI Frontier Tier (Autonomous Agent Pipeline)",
            "file": "copilot/samples/sample_openai.csv",
            "plan_text": "Expanding European cluster deployment next month (+35% traffic) and optimizing prompt context caching in month 3 (-20% load).",
            "spot": 5.00,
            "fwd": 3.63,
            "sample_prompts": [
                "Summarize daily engineering ticket activity",
                "Extract structured billing invoice details from PDF",
                "Classify user chat intent across 40 customer categories",
                "Prove Godel incompleteness theorem with formal lean4 code",
                "Draft routine product changelog from commit messages"
            ]
        },
        {
            "id": "anthropic_tier",
            "name": "Anthropic Claude 3.5 Sonnet Tier (Coding Fleet)",
            "file": "copilot/samples/sample_anthropic.csv",
            "plan_text": "Scaling engineering team to 50 active coding copilot seats with +45% query volume.",
            "spot": 3.00,
            "fwd": 2.18,
            "sample_prompts": [
                "Refactor React component to modern functional hooks",
                "Generate pytest test cases for FastAPI router endpoints",
                "Formulate non-convex multi-objective portfolio optimizer in C++",
                "Review git pull request diff for memory leaks",
                "Write SQL migration script adding composite index"
            ]
        },
        {
            "id": "openrouter_tier",
            "name": "OpenRouter Fleet Aggregator (Multi-Model Gateway)",
            "file": "copilot/samples/sample_openrouter.csv",
            "plan_text": "Ramping up customer synthetic data generation (+60% tokens) with scheduled fine-tuning freeze (-15% volume).",
            "spot": 4.00,
            "fwd": 2.90,
            "sample_prompts": [
                "Translate English product description to 12 target languages",
                "Synthesize realistic user dialogues for customer support training",
                "Verify complex formal mathematical proof with Coq tactics",
                "Categorize customer reviews into sentiment taxonomy",
                "Summarize legal contract privacy policies into checklist"
            ]
        }
    ]
    
    for p_cfg in preset_configs:
        with open(p_cfg["file"], "r", encoding="utf-8") as f:
            csv_text = f.read()
        parsed = parse_usage_csv(csv_text)
        plans = extract_demand_plans(p_cfg["plan_text"])
        forecast = generate_demand_forecast(
            parsed.daily_tokens_millions,
            plans,
            horizon_days=90,
            num_scenarios=4000,
            random_seed=42
        )
        rec = compute_optimal_contract_order(
            forecast,
            spot_initial=p_cfg["spot"],
            fair_fwd_price=p_cfg["fwd"],
            crunch_spread_pct=0.358
        )
        fit_res = evaluate_prompt_fit(
            p_cfg["sample_prompts"],
            frontier_cost_per_m=p_cfg["spot"],
            cheaper_cost_per_m=p_cfg["fwd"]
        )
        explanation = generate_copilot_explanation(rec, parsed, forecast)
        
        step = 3
        days_sampled = list(range(0, forecast.horizon_days, step))
        if days_sampled[-1] != forecast.horizon_days - 1:
            days_sampled.append(forecast.horizon_days - 1)
            
        copilot_presets[p_cfg["id"]] = {
            "id": p_cfg["id"],
            "name": p_cfg["name"],
            "plan_text": p_cfg["plan_text"],
            "parsed": {
                "num_days": parsed.num_days,
                "total_tokens_m": round(parsed.total_tokens_millions, 1),
                "mean_daily_m": round(parsed.mean_daily_tokens_millions, 2),
                "daily_volatility": round(parsed.std_daily_tokens_millions, 3)
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
                "expected_total_m": round(forecast.expected_total_demand_m, 1),
                "p10_total_m": round(forecast.p10_total_demand_m, 1),
                "p90_total_m": round(forecast.p90_total_demand_m, 1),
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
        
    parity_data = {}
    for p_name, p_file in [
        ("substitutability", "data/parity/substitutability_matrix.json"),
        ("obsolescence", "data/parity/obsolescence_curves.json"),
        ("valuation", "data/parity/valuation_curves.json"),
        ("clearing", "data/parity/clearing_results.json"),
        ("seller", "data/parity/seller_curves.json"),
        ("procurement", "data/parity/procurement_results.json")
    ]:
        if os.path.exists(p_file):
            with open(p_file, "r", encoding="utf-8") as pf:
                parity_data[p_name] = json.load(pf)

    site_payload = {
        "models": models_dict,
        "headline_experiment": headline_data,
        "crunch_comparison": crunch_comparison,
        "empirical_migration": empirical_migration,
        "copilot_presets": copilot_presets,
        "parity": parity_data
    }
    
    json_path = os.path.join("web", "data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(site_payload, f, indent=2)
        
    js_path = os.path.join("web", "data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.EMBEDDED_SITE_DATA = " + json.dumps(site_payload, indent=2) + ";\n")

if __name__ == "__main__":
    main()
