from stampede.types import Quantity, Provenance
from stampede.stages.narrative import generate_narrative, verify_and_bind_narrative

def test_grounding_rejects_hallucinated_numbers():
    quantities = {
        "baseline_spend_usd": Quantity(value=10000.0, provenance=Provenance.MEASURED_LIVE),
        "total_spend_usd": Quantity(value=7000.0, provenance=Provenance.FITTED)
    }
    unverified_text = "We spent $99,999.00 on infrastructure with 45.2% savings."
    is_grounded, bindings, unverified = verify_and_bind_narrative(unverified_text, quantities)
    assert not is_grounded
    assert len(unverified) > 0

def test_templated_narrative_is_fully_grounded():
    quantities = {
        "baseline_spend_usd": Quantity(value=10000.0, provenance=Provenance.MEASURED_LIVE),
        "total_spend_usd": Quantity(value=7500.0, provenance=Provenance.FITTED),
        "total_saving_usd": Quantity(value=2500.0, provenance=Provenance.FITTED),
        "risk_adjusted_saving_usd": Quantity(value=2200.0, provenance=Provenance.FITTED),
        "optimal_sizing_q_star": Quantity(value=500.0, provenance=Provenance.FITTED)
    }
    res = generate_narrative(quantities, gateway=None)
    assert res.is_grounded
    assert len(res.bindings) >= 4
    assert res.render_mode == "templated"

def test_narrative_repair_attempt_and_fallback():
    from tests.support.fake_models import FakeGateway
    quantities = {
        "baseline_spend_usd": Quantity(value=10000.0, provenance=Provenance.MEASURED_LIVE),
        "total_spend_usd": Quantity(value=7500.0, provenance=Provenance.FITTED),
        "total_saving_usd": Quantity(value=2500.0, provenance=Provenance.FITTED),
        "risk_adjusted_saving_usd": Quantity(value=2200.0, provenance=Provenance.FITTED),
        "optimal_sizing_q_star": Quantity(value=500.0, provenance=Provenance.FITTED)
    }
    gateway = FakeGateway(api_key="sk-test-key")
    call_count = 0
    def mock_complete(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {"content": "Spend was $10000.00 but we saved $99999.00 miraculously."}
        return {"content": "Baseline is $10000.00 and commitment spend is $7500.00 with saving $2500.00."}
    gateway.complete = mock_complete
    res = generate_narrative(quantities, gateway=gateway)
    assert call_count == 2
    assert res.is_grounded is True
    assert res.render_mode == "llm_generated"

def test_narrative_falls_back_after_two_failures():
    from tests.support.fake_models import FakeGateway
    quantities = {
        "baseline_spend_usd": Quantity(value=10000.0, provenance=Provenance.MEASURED_LIVE),
        "total_spend_usd": Quantity(value=7500.0, provenance=Provenance.FITTED),
        "total_saving_usd": Quantity(value=2500.0, provenance=Provenance.FITTED),
        "risk_adjusted_saving_usd": Quantity(value=2200.0, provenance=Provenance.FITTED),
        "optimal_sizing_q_star": Quantity(value=500.0, provenance=Provenance.FITTED)
    }
    gateway = FakeGateway(api_key="sk-test-key")
    gateway.complete = lambda **kwargs: {"content": "Ungrounded $99999.00 constantly."}
    res = generate_narrative(quantities, gateway=gateway)
    assert res.is_grounded is True
    assert "template" in res.render_mode

def test_rfq_grounding_and_repair():
    from tests.support.fake_models import FakeGateway
    from stampede.stages.rfq import StructuredRFQ, AcceptableModelSpec, render_rfq_email_with_llm
    rfq = StructuredRFQ(
        rfq_id="rfq_test",
        workload_mix={"json": 1.0},
        measured_tokens_per_task={"json": 100},
        acceptable_models=[AcceptableModelSpec(model="gpt-4o", min_parity_threshold=0.90, measured_parity_score=0.95)],
        tenor_days=90,
        quantity_min=100.0,
        quantity_max=200.0,
        max_strike_per_token_usd=0.000025,
        resale_clause_required=True,
        conversion_clause_required=False,
        delivery_profile={"q1": 50.0},
        evaluation_criteria=["SLA"]
    )
    gateway = FakeGateway(api_key="sk-test-key")
    gateway.complete = lambda **kwargs: {"content": "Tenor: 90 days, Quantity range: 100.0 to 200.0, Max strike: $0.000025, Model: gpt-4o."}
    email = render_rfq_email_with_llm(rfq, gateway=gateway)
    assert "90 days" in email
    assert "100.0" in email
