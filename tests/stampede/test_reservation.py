import math
from stampede.stages.valuation_live import (
    compute_reservation_prices_table,
    CATALOG_SPOTS
)
from stampede.stages.quotes_rank import rank_quotes_risk_adjusted

def test_reservation_prices_coverage_and_provenance():
    models = list(CATALOG_SPOTS.keys())
    tenors = [30, 60, 90]
    table = compute_reservation_prices_table(models=models, tenors=tenors)

    assert len(table) == len(models) * len(tenors)
    for rec in table:
        assert rec.model in models
        assert rec.tenor_days in tenors
        assert rec.params_source == "assumed_v1"
        assert rec.column_label == "Do not sign below this discount, under these assumptions."
        assert rec.mc_standard_error_pct > 0.0
        assert 0.0 < rec.reservation_discount_pct.value < 100.0

def test_reservation_price_quote_ranking_consistency():
    models = ["openai/gpt-4o"]
    table = compute_reservation_prices_table(models=models, tenors=[90], risk_aversion=0.25)
    rec = table[0]

    d_star = rec.reservation_discount_pct.value
    s0 = rec.spot_initial
    se_pct = rec.mc_standard_error_pct

    cap_tokens = 1000.0
    f_star = s0 * (1.0 - d_star / 100.0)

    t_yr = 90 / 365.0
    drift = -0.25
    hazard_drag = 0.48
    vol = 0.22
    exp_spot = s0 * math.exp((drift - hazard_drag) * t_yr)
    var_spot = (s0 ** 2) * (math.exp((vol ** 2) * t_yr) - 1.0) + (s0 ** 2) * (0.16 * t_yr)
    sd_spot = math.sqrt(max(1e-6, var_spot))

    exp_saving_per_m = exp_spot - f_star * (1.0 + 0.20 * 0.12 * t_yr)
    total_exp_saving = exp_saving_per_m * cap_tokens
    total_sd = sd_spot * cap_tokens

    risk_adj_saving = total_exp_saving - (0.25 * total_sd)
    se_usd = (se_pct / 100.0) * s0 * cap_tokens

    assert abs(risk_adj_saving) <= 2.0 * se_usd
