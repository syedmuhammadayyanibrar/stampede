from stampede.stages.quotes_parse import parse_quotes_text

def test_quote_parsing_with_verbatim_evidence():
    text = (
        "Quote from Anthropic for claude-3-5-sonnet: 25.0% discount on $3.00 list price. "
        "Tenor 90 days, prepay 20%, size 50000 tokens."
    )
    quotes = parse_quotes_text(text)
    assert len(quotes) >= 1
    q = quotes[0]
    assert q.provider.lower() == "anthropic"
    assert q.discount_pct == 25.0
    assert q.tenor_days == 90
    assert "25.0%" in q.evidence_quotes["discount_pct"]
