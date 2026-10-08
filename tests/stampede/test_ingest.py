import pytest
from stampede.stages.ingest import (
    parse_usage_input,
    generate_synthetic_usage_series,
    check_ingestion_invariants,
    ingest_usage_csv
)
from tests.support.fake_models import FakeGateway

def test_deterministic_v1_csv_parsing():
    rows = ["date,total_tokens"] + [f"2026-01-{i:02d},1000000" for i in range(1, 15)]
    csv_text = "\n".join(rows)
    res = parse_usage_input(csv_text)
    assert len(res.tokens_series.values) == 14
    assert res.success

def test_synthetic_usage_generation():
    res = generate_synthetic_usage_series(days=60, base_daily_tokens=50000.0)
    assert len(res.tokens_series.values) == 60
    assert all(v > 0 for v in res.tokens_series.values)
    assert res.total_tokens_m.provenance.value == "SIMULATED"
    assert res.total_tokens_m.note == "USER_INPUT-derived"

def test_invariant_rejection_empty_input():
    res = parse_usage_input("")
    assert not res.success

def test_invariant_minimum_14_days_rejection():
    dates = [f"2026-01-{i:02d}" for i in range(1, 10)]
    tokens = [1.0] * len(dates)
    passed, err = check_ingestion_invariants(dates, tokens, sum(tokens))
    assert passed is False
    assert "14 distinct days required" in str(err)

def test_invariant_duplicate_dates_rejection():
    dates = [f"2026-01-{i:02d}" for i in range(1, 15)] + ["2026-01-01", "2026-01-02"]
    tokens = [1.0] * len(dates)
    passed, err = check_ingestion_invariants(dates, tokens, sum(tokens))
    assert passed is False
    assert "Duplicate date rate" in str(err)

def test_invariant_negative_tokens_rejection():
    dates = [f"2026-01-{i:02d}" for i in range(1, 16)]
    tokens = [1.0] * 14 + [-5.0]
    passed, err = check_ingestion_invariants(dates, tokens, sum(tokens))
    assert passed is False
    assert "Negative token count" in str(err)

def test_invariant_sum_deviation_rejection():
    dates = [f"2026-01-{i:02d}" for i in range(1, 16)]
    tokens = [1.0] * 15
    passed, err = check_ingestion_invariants(dates, tokens, 20.0)
    assert passed is False
    assert "differs from reported" in str(err)

def test_corrupted_csv_llm_mapping_fallback():
    import json
    rows = ["timestamp_day,tokens_consumed,model_name"] + [f"2026-02-{i:02d},500000,gpt-4o" for i in range(1, 16)]
    csv_text = "\n".join(rows)
    gateway = FakeGateway(api_key="sk-test-key")
    mapping_payload = json.dumps({
        "date_column": "timestamp_day",
        "tokens_column": "tokens_consumed",
        "model_column": "model_name",
        "token_unit_multiplier": 1.0
    })
    gateway.complete = lambda **kwargs: {"content": mapping_payload}
    res = ingest_usage_csv(csv_text, gateway=gateway)
    assert res.success is True
    assert res.method == "llm_mapped"
    assert res.num_days == 15
    assert res.invariants_passed is True

def test_silent_wrong_accept_rejection():
    import json
    rows = ["timestamp_day,tokens_consumed,model_name"] + [f"2026-02-{i:02d},-1000,gpt-4o" for i in range(1, 16)]
    csv_text = "\n".join(rows)
    gateway = FakeGateway(api_key="sk-test-key")
    mapping_payload = json.dumps({
        "date_column": "timestamp_day",
        "tokens_column": "tokens_consumed",
        "model_column": "model_name",
        "token_unit_multiplier": 1.0
    })
    gateway.complete = lambda **kwargs: {"content": mapping_payload}
    res = ingest_usage_csv(csv_text, gateway=gateway)
    assert res.success is False
    assert res.invariants_passed is False
    assert "Negative token count" in str(res.error)
