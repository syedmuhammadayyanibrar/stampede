from stampede.stages.quotes_rank import rank_quotes_risk_adjusted

def test_quotes_ranking_order_and_properties():
    raw_quotes = [
        {
            "quote_id": "q1",
            "provider": "ProviderA",
            "model": "model-1",
            "annual_token_allowance": 100000.0,
            "annual_prepay_usd": 1000.0,
            "prepay_share": 0.10,
            "tenor_days": 90,
            "effective_unit_cost": 2.50,
            "discount_pct": 35.0,
            "resale_allowed": True,
            "conversion_clause": False
        },
        {
            "quote_id": "q2",
            "provider": "ProviderB",
            "model": "model-2",
            "annual_token_allowance": 100000.0,
            "annual_prepay_usd": 1500.0,
            "prepay_share": 0.20,
            "tenor_days": 90,
            "effective_unit_cost": 3.80,
            "discount_pct": 10.0,
            "resale_allowed": False,
            "conversion_clause": False
        }
    ]
    ranked = rank_quotes_risk_adjusted(raw_quotes, rho=0.5)
    assert len(ranked) == 2
    assert ranked[0].quote_id == "q1"
    assert ranked[0].expected_net_saving_usd >= ranked[1].expected_net_saving_usd
