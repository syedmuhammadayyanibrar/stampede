from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from stampede.types import Quantity, Provenance

class WaterfallBar(BaseModel):
    name: str
    label: str
    value_usd: float
    share_of_baseline: float
    cumulative_usd: float

class NetSavingWaterfall(BaseModel):
    baseline_spend_usd: float
    full_valuation_usd: float
    full_valuation_share: float
    bars: List[WaterfallBar]
    is_exact_sum: bool
    residual_error: float
    note: str = "Step order affects bar values. /explain provides order-free Shapley attribution."

def compute_net_saving_waterfall(
    covered_volume_tokens_m: float,
    incumbent_spot_per_m: float = 5.00,
    quote_strike_per_m: float = 3.50,
    quality_score: float = 0.95,
    deflation_pct: float = 12.0,
    prepay_pct: float = 20.0,
    cost_of_capital_rate: float = 0.10,
    tenor_days: int = 90,
    shutdown_hazard_prob: float = 0.15,
    shutdown_loss_per_m: float = 1.20,
    resale_recovery_per_m: float = 0.85,
    conversion_boost_per_m: float = 0.25
) -> NetSavingWaterfall:
    b_spend = incumbent_spot_per_m * covered_volume_tokens_m

    headline_saving_unit = incumbent_spot_per_m - quote_strike_per_m
    val_headline = headline_saving_unit * covered_volume_tokens_m

    effective_strike = quote_strike_per_m / max(0.01, quality_score)
    val_v0 = (incumbent_spot_per_m - effective_strike) * covered_volume_tokens_m
    val_quality = val_v0 - val_headline

    def_decay = deflation_pct / 100.0
    val_v1 = val_v0 - (def_decay * incumbent_spot_per_m * covered_volume_tokens_m)

    t_yr = tenor_days / 365.0
    fin_cost = (prepay_pct / 100.0) * quote_strike_per_m * cost_of_capital_rate * t_yr * covered_volume_tokens_m
    val_v2 = val_v1 - fin_cost

    shutdown_loss = shutdown_hazard_prob * shutdown_loss_per_m * covered_volume_tokens_m
    val_v3 = val_v2 - shutdown_loss

    resale_gain = (resale_recovery_per_m + conversion_boost_per_m) * covered_volume_tokens_m
    val_v4 = val_v3 + resale_gain

    full_val = val_v4

    bar_definitions = [
        ("headline_discount", "Headline Discount", val_headline),
        ("quality_adjustment", "Quality Adjustment", val_quality),
        ("price_deflation", "Price Deflation (V1 - V0)", val_v1 - val_v0),
        ("prepay_financing", "Prepay Financing (V2 - V1)", val_v2 - val_v1),
        ("shutdown_exposure", "Shutdown & Obsolescence (V3 - V2)", val_v3 - val_v2),
        ("resale_recovery", "Resale & Conversion Recovery (V4 - V3)", val_v4 - val_v3)
    ]

    bars = []
    cum = 0.0
    for key, label, val in bar_definitions:
        cum += val
        bars.append(WaterfallBar(
            name=key,
            label=label,
            value_usd=float(val),
            share_of_baseline=float(val / max(1e-9, b_spend)),
            cumulative_usd=float(cum)
        ))

    sum_bars = sum(b.value_usd for b in bars)
    residual = abs(sum_bars - full_val)
    is_exact = residual < 1e-9

    return NetSavingWaterfall(
        baseline_spend_usd=float(b_spend),
        full_valuation_usd=float(full_val),
        full_valuation_share=float(full_val / max(1e-9, b_spend)),
        bars=bars,
        is_exact_sum=is_exact,
        residual_error=residual
    )
