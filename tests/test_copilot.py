import pytest
import os
from copilot.parser import parse_usage_csv
from copilot.plans import extract_demand_plans
from copilot.forecast import generate_demand_forecast
from copilot.sizing import compute_optimal_contract_order
from copilot.fit_check import evaluate_prompt_fit
from copilot.explain import ground_numbers_check, generate_copilot_explanation

def test_parse_sample_csvs():
    samples_dir = "copilot/samples"
    for fname in ("sample_openai.csv", "sample_anthropic.csv", "sample_openrouter.csv"):
        fpath = os.path.join(samples_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        res = parse_usage_csv(content)
        assert res.success is True
        assert res.num_days >= 30
        assert res.total_tokens_millions > 100.0
        assert res.mean_daily_tokens_millions > 0.0

def test_parse_invalid_csv():
    assert parse_usage_csv("").success is False
    assert parse_usage_csv("col1,col2\nval1,val2").success is False

def test_plan_extraction_verification():
    raw_text = "We are planning a European launch next month (+35% traffic) and optimizing caching in month 3 (-20% load)."
    events = extract_demand_plans(raw_text)
    assert len(events) >= 2
    for ev in events:
        assert ev.source_quote.lower() in raw_text.lower() or any(w.lower() in raw_text.lower() for w in ev.source_quote.split())

def test_forecast_and_sizing():
    daily_hist = [10.0, 10.5, 10.2, 10.8, 11.2, 11.5, 11.8, 12.0]
    raw_text = "European launch (+25% volume)"
    events = extract_demand_plans(raw_text)
    
    fc = generate_demand_forecast(daily_hist, events, horizon_days=30, num_scenarios=2000, random_seed=42)
    assert fc.horizon_days == 30
    assert fc.expected_total_demand_m > 300.0
    assert len(fc.p10_daily_m) == 30
    
    rec = compute_optimal_contract_order(fc, spot_initial=5.00, fair_fwd_price=3.63, crunch_spread_pct=0.358)
    assert rec.optimal_notional_m > 0.0
    assert rec.expected_savings > 0.0
    assert rec.savings_pct > 15.0

def test_fit_check():
    prompts = [
        "Extract invoice items from table",
        "Classify user intent",
        "Prove Godel incompleteness theorem with full mathematical rigor"
    ]
    res = evaluate_prompt_fit(prompts)
    assert res.total_prompts == 3
    assert res.sufficient_count == 2
    assert res.sufficiency_rate_pct == 66.7
    assert res.dollar_savings_per_m > 0.0

def test_ground_numbers():
    allowed = [100.0, 50.0, 3.63, 150000.0]
    valid_text = "Contract covers 100M tokens at $3.63 with $150,000 savings over 30 days."
    invalid_text = "Contract covers 100M tokens at $9.99 with $999,999 savings."
    assert ground_numbers_check(valid_text, allowed) is True
    assert ground_numbers_check(invalid_text, allowed) is False
