from stampede.stages.quotes_rank import rank_quotes_risk_adjusted

def test_quote_sensitivity_to_discount():
    q_base = [{
        "quote_id": "q1",
        "provider": "TestProv",
        "model": "model-a",
        "committed_capacity": 10000.0,
        "discount_pct": 20.0,
        "effective_unit_cost": 3.00,
        "resale_allowed": True,
        "conversion_clause": False
    }]
    q_higher = [{
        "quote_id": "q1",
        "provider": "TestProv",
        "model": "model-a",
        "committed_capacity": 10000.0,
        "discount_pct": 40.0,
        "effective_unit_cost": 3.00,
        "resale_allowed": True,
        "conversion_clause": False
    }]
    r_base = rank_quotes_risk_adjusted(q_base)[0]
    r_high = rank_quotes_risk_adjusted(q_higher)[0]
    assert r_high.expected_net_saving_usd > r_base.expected_net_saving_usd
