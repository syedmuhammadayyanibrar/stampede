from stampede.stages.waterfall import compute_net_saving_waterfall

def test_waterfall_telescoping_exact_sum():
    wf = compute_net_saving_waterfall(
        covered_volume_tokens_m=20.0,
        incumbent_spot_per_m=5.00,
        quote_strike_per_m=3.50,
        quality_score=0.92,
        deflation_pct=15.0,
        prepay_pct=25.0,
        cost_of_capital_rate=0.12,
        tenor_days=90,
        shutdown_hazard_prob=0.10,
        shutdown_loss_per_m=1.00,
        resale_recovery_per_m=0.75,
        conversion_boost_per_m=0.20
    )
    assert wf.is_exact_sum is True
    assert wf.residual_error < 1e-9
    assert len(wf.bars) == 6

def test_waterfall_bar_signs_on_constructed_inputs():
    wf = compute_net_saving_waterfall(
        covered_volume_tokens_m=10.0,
        incumbent_spot_per_m=5.00,
        quote_strike_per_m=3.50,
        quality_score=0.90,
        deflation_pct=10.0,
        prepay_pct=20.0,
        cost_of_capital_rate=0.10,
        tenor_days=90,
        shutdown_hazard_prob=0.08,
        shutdown_loss_per_m=1.00,
        resale_recovery_per_m=0.80,
        conversion_boost_per_m=0.10
    )
    bars_dict = {b.name: b.value_usd for b in wf.bars}

    assert bars_dict["headline_discount"] > 0.0
    assert bars_dict["quality_adjustment"] <= 0.0
    assert bars_dict["price_deflation"] <= 0.0
    assert bars_dict["prepay_financing"] <= 0.0
    assert bars_dict["shutdown_exposure"] <= 0.0
    assert bars_dict["resale_recovery"] >= 0.0

def test_waterfall_ui_disclaimer_present():
    wf = compute_net_saving_waterfall(covered_volume_tokens_m=5.0)
    assert "Shapley" in wf.note
    assert "/explain" in wf.note
