import pytest
from stampede.stages.quotes_parse import (
    parse_discount_from_snippet,
    extract_evidence_quoted_field,
    parse_quotes_structured
)

def test_discount_parsing_in_range_and_notices():
    val, err, notc = parse_discount_from_snippet("0% discount")
    assert val == 0.0
    assert err is None
    assert notc is not None
    assert notc.code == "DISCOUNT_OUTSIDE_TYPICAL"

    val, err, notc = parse_discount_from_snippet("5% discount")
    assert val == 5.0
    assert err is None
    assert notc is not None
    assert notc.code == "DISCOUNT_OUTSIDE_TYPICAL"

    val, err, notc = parse_discount_from_snippet("25% discount")
    assert val == 25.0
    assert err is None
    assert notc is None

    val, err, notc = parse_discount_from_snippet("45% discount")
    assert val == 45.0
    assert err is None
    assert notc is not None
    assert notc.code == "DISCOUNT_OUTSIDE_TYPICAL"

    val, err, notc = parse_discount_from_snippet("95% discount")
    assert val == 95.0
    assert err is None
    assert notc is not None
    assert notc.code == "DISCOUNT_OUTSIDE_TYPICAL"

def test_discount_parsing_out_of_range_rejected():
    val, err, notc = parse_discount_from_snippet("-5% discount")
    assert val is None
    assert err == "INVALID_DISCOUNT_RANGE"

    val, err, notc = parse_discount_from_snippet("120% discount")
    assert val is None
    assert err == "INVALID_DISCOUNT_RANGE"

def test_discount_words_and_decimal_representation():
    val, err, notc = parse_discount_from_snippet("twenty five percent discount")
    assert val == 25.0
    assert err is None
    assert notc is None

    val, err, notc = parse_discount_from_snippet("0.25 rate")
    assert val == 25.0
    assert err is None
    assert notc is None

def test_verbatim_evidence_quote_verification():
    source = "Provider Anthropic offers 25% discount for 90 days."
    valid, err = extract_evidence_quoted_field(source, "25% discount", 25.0)
    assert valid is True
    assert err is None

    valid, err = extract_evidence_quoted_field(source, "40% discount hallucinated", 40.0)
    assert valid is False
    assert err is not None

def test_quote_parser_marks_unverified_field():
    text = "Anthropic agrees to 25% discount for 90 days."
    res = parse_quotes_structured(text)
    assert len(res.quotes) >= 1
    assert res.quotes[0].discount_pct == 25.0
    assert "25%" in res.quotes[0].evidence_quotes["discount_pct"]
