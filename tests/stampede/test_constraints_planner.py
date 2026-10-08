import json
from stampede.stages.constraints_parse import (
    parse_constraints_deterministic,
    parse_constraints,
    ConstraintItem,
    ParsedConstraints
)
from stampede.stages.planner import solve_plan
from tests.support.fake_models import FakeGateway

def test_constraint_parsing_and_hard_flag():
    text = (
        "We must exclude anthropic from our infrastructure.\n"
        "Budget cannot exceed $50,000.\n"
        "Minimum parity 0.92 is required."
    )
    res = parse_constraints_deterministic(text)
    assert len(res.items) >= 3
    excluded = res.get_value("excluded_providers")
    assert "anthropic" in excluded
    assert res.get_value("max_spend_usd") == 50000.0
    for it in res.items:
        assert it.is_hard is True

def test_verbatim_evidence_drops_unsupported_constraint():
    text = "We must exclude anthropic."
    res = parse_constraints_deterministic(text)
    assert len(res.items) == 1
    assert "anthropic" in res.get_value("excluded_providers")

    raw_fake = [
        {"field": "max_spend_usd", "value": 1000.0, "is_hard": True, "evidence_quote": "nonexistent text in input"}
    ]
    items = []
    unparsed = []
    norm_text = " ".join(text.split()).lower()
    for d in raw_fake:
        q = d["evidence_quote"]
        norm_q = " ".join(q.split()).lower()
        if q and norm_q in norm_text:
            items.append(ConstraintItem(**d))
        else:
            unparsed.append(str(d))
    parsed = ParsedConstraints(items=items, unparsed_remainder=unparsed, raw_text=text)
    assert len(parsed.items) == 0
    assert len(parsed.unparsed_remainder) == 1

def test_planner_respects_hard_exclusion():
    quotes = [
        {
            "quote_id": "q_anthropic",
            "provider": "Anthropic",
            "model": "claude-3-5-sonnet",
            "committed_capacity": 500.0,
            "effective_unit_cost": 2.00,
            "expected_net_saving_usd": 3000.0,
            "sd_saving_usd": 100.0
        }
    ]
    constraints = parse_constraints_deterministic("must exclude Anthropic")
    plan = solve_plan(quotes_ranked=quotes, q_star=500.0, baseline_spend=2500.0, constraints=constraints)
    assert len(plan.rejected_options) == 1
    assert plan.rejected_options[0].binding_constraint == "excluded_providers"
    assert plan.allocations[0].option_id == "stay_on_demand"

def test_planner_records_binding_reasons_for_all_rejected_options():
    quotes = [
        {
            "quote_id": "q_expensive",
            "provider": "OpenAI",
            "model": "gpt-4o",
            "committed_capacity": 1000.0,
            "effective_unit_cost": 10.0,
            "expected_net_saving_usd": 1000.0,
            "sd_saving_usd": 50.0,
            "tenor_days": 180,
            "prepay_share": 0.50
        }
    ]
    constraints = parse_constraints_deterministic(
        "Budget cannot exceed $500.\n"
        "Tenor at most 90 days.\n"
        "Prepay at most 20%."
    )
    plan = solve_plan(quotes_ranked=quotes, q_star=500.0, baseline_spend=5000.0, constraints=constraints)
    assert len(plan.rejected_options) >= 1
    binding_constraints = [r.binding_constraint for r in plan.rejected_options]
    assert any(b in ("max_tenor_days", "max_prepay_pct", "max_spend_usd") for b in binding_constraints)

def test_planner_zero_quotes_fallback():
    plan = solve_plan(quotes_ranked=[], q_star=500.0, baseline_spend=2500.0, constraints=None)
    assert len(plan.allocations) == 1
    assert plan.allocations[0].option_id == "stay_on_demand"
    assert plan.optimal_sizing_q_star.value == 500.0

def test_parse_constraints_with_fake_gateway():
    gateway = FakeGateway(api_key="sk-test-key")
    text = "We must exclude anthropic. Budget cannot exceed $25,000. Tenor at most 60 days."
    mock_json = json.dumps([
        {"field": "excluded_providers", "value": ["anthropic"], "is_hard": True, "evidence_quote": "must exclude anthropic"},
        {"field": "max_spend_usd", "value": 25000.0, "is_hard": True, "evidence_quote": "Budget cannot exceed $25,000"},
        {"field": "max_tenor_days", "value": 60, "is_hard": True, "evidence_quote": "Tenor at most 60 days"}
    ])
    gateway.complete = lambda **kwargs: {"content": mock_json}
    res = parse_constraints(text, gateway=gateway)
    assert res.method == "llm_parsed"
    assert len(res.items) == 3
    assert res.get_value("excluded_providers") == ["anthropic"]
    assert res.get_value("max_spend_usd") == 25000.0
    assert res.get_value("max_tenor_days") == 60
    assert all(it.is_hard for it in res.items)

def test_planner_respects_hard_constraints_across_200_scenarios():
    import random
    rng = random.Random(2026)
    providers = ["openai", "anthropic", "together", "cohere", "aws"]
    models = ["gpt-4o", "claude-3-5-sonnet", "mistral-large", "command-r", "llama-3-70b"]

    for sc_idx in range(200):
        exc_p = rng.sample(providers, k=rng.randint(0, 2))
        max_sp = rng.uniform(1000.0, 50000.0)
        min_p = rng.uniform(0.70, 0.95)
        max_t = rng.randint(30, 180)
        max_pr = rng.uniform(0.10, 0.50)
        req_res = rng.choice([True, False])
        req_conv = rng.choice([True, False])

        c_items = [
            ConstraintItem(field="excluded_providers", value=exc_p, is_hard=True, evidence_quote="mock quote"),
            ConstraintItem(field="max_spend_usd", value=max_sp, is_hard=True, evidence_quote="mock quote"),
            ConstraintItem(field="min_parity", value=min_p, is_hard=True, evidence_quote="mock quote"),
            ConstraintItem(field="max_tenor_days", value=max_t, is_hard=True, evidence_quote="mock quote"),
            ConstraintItem(field="max_prepay_pct", value=max_pr, is_hard=True, evidence_quote="mock quote"),
            ConstraintItem(field="require_resale", value=req_res, is_hard=True, evidence_quote="mock quote"),
            ConstraintItem(field="require_conversion", value=req_conv, is_hard=True, evidence_quote="mock quote")
        ]
        constraints = ParsedConstraints(items=c_items, raw_text="mock", method="deterministic")

        num_quotes = rng.randint(1, 5)
        quotes = []
        for q_i in range(num_quotes):
            p = rng.choice(providers)
            m = rng.choice(models)
            tenor = rng.randint(20, 200)
            prepay = rng.uniform(0.05, 0.60)
            resale = rng.choice([True, False])
            conv = rng.choice([True, False])
            parity = rng.uniform(0.65, 0.99)
            quotes.append({
                "quote_id": f"q_{sc_idx}_{q_i}",
                "provider": p,
                "model": m,
                "tenor_days": tenor,
                "prepay_share": prepay,
                "resale_allowed": resale,
                "conversion_clause": conv,
                "parity_score": parity,
                "committed_capacity": rng.uniform(100.0, 1000.0),
                "effective_unit_cost": rng.uniform(1.0, 5.0),
                "expected_net_saving_usd": rng.uniform(-1000.0, 10000.0),
                "sd_saving_usd": rng.uniform(10.0, 500.0)
            })

        plan = solve_plan(quotes_ranked=quotes, q_star=500.0, baseline_spend=25000.0, constraints=constraints)
        for alloc in plan.allocations:
            if alloc.option_type == "committed_quote":
                matching_q = next((q for q in quotes if alloc.option_id.startswith(q["quote_id"])), None)
                if matching_q:
                    assert matching_q["provider"].lower() not in [x.lower() for x in exc_p]
                    assert alloc.expected_spend_usd <= max_sp + 1e-4
                    assert matching_q["parity_score"] >= min_p - 1e-4
                    assert matching_q["tenor_days"] <= max_t
                    assert matching_q["prepay_share"] <= max_pr + 1e-4
                    if req_res:
                        assert matching_q["resale_allowed"] is True
                    if req_conv:
                        assert matching_q["conversion_clause"] is True
