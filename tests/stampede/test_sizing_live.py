from stampede.stages.sizing_live import calculate_live_sizing

def test_newsvendor_sizing_hand_calculation():
    sz = calculate_live_sizing(
        mean_demand=1000.0,
        sd_demand=200.0,
        on_demand_rate=5.00,
        committed_rate=3.50,
        salvage_rate=1.50
    )
    cu = 5.00 - 3.50
    co = 3.50 - 1.50
    expected_ratio = cu / (cu + co)
    assert abs(sz.critical_ratio.value - expected_ratio) < 1e-4
    assert sz.optimal_sizing_tokens.value > 0
