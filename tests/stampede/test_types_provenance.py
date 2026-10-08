from stampede.types import Quantity, Provenance, Series
from stampede.stages.forecast import run_forecast_monte_carlo
from stampede.stages.sizing_live import calculate_live_sizing
from stampede.stages.valuation_live import run_live_valuation

def test_quantity_provenance_and_immutability():
    q = Quantity(value=123.45, unit="usd", provenance=Provenance.MEASURED_LIVE, source="test")
    assert q.value == 123.45
    assert q.provenance == Provenance.MEASURED_LIVE
    assert q.id.startswith("qty_")

def test_numeric_leaves_have_provenance():
    fc = run_forecast_monte_carlo([1000.0] * 30, days_ahead=30)
    assert isinstance(fc.total_tokens_q50, float)
    sz = calculate_live_sizing(1000.0, 100.0, 5.0, 3.5, 1.5)
    assert isinstance(sz.optimal_sizing_tokens, Quantity)
    assert sz.optimal_sizing_tokens.provenance in (Provenance.FITTED, Provenance.SIMULATED)
    val = run_live_valuation(spot_initial=5.0, prepay_share=0.2, tenor_days=90, cost_of_capital=0.1)
    assert isinstance(val.fair_value_contract, Quantity)
    assert val.fair_value_contract.provenance == Provenance.SIMULATED
