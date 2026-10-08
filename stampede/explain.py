from typing import Dict, Any
from pydantic import BaseModel
from parity.valuation.shapley import compute_exact_shapley_decomposition
from stampede.types import Quantity, Provenance

class ShapleyFactorAttribution(BaseModel):
    factor_name: str
    contribution_usd: Quantity
    contribution_share_pct: Quantity

class ExplainReport(BaseModel):
    target: str
    total_value_usd: Quantity
    factors: Dict[str, ShapleyFactorAttribution]
    efficiency_residual: Quantity
    is_efficient: bool

def generate_shapley_explanation(
    target: str = "net_discount",
    spot_initial: float = 5.00,
    drift: float = -0.35,
    volatility: float = 0.28,
    hazard_rate: float = 1.85,
    jump_mean: float = 0.45,
    spread: float = 0.06,
    tenor_days: int = 90
) -> ExplainReport:
    raw_shapley = compute_exact_shapley_decomposition(
        spot_initial=spot_initial,
        drift=drift,
        volatility=volatility,
        hazard_rate=hazard_rate,
        jump_mean=jump_mean,
        spread=spread,
        tenor_days=tenor_days
    )

    tot_val = raw_shapley["grand_coalition_value"]
    factors_map = {}
    for f_name, f_val in raw_shapley["shapley_values"].items():
        share = (f_val / max(1e-6, tot_val)) * 100.0 if tot_val > 0 else 20.0
        factors_map[f_name] = ShapleyFactorAttribution(
            factor_name=f_name,
            contribution_usd=Quantity(
                id=f"shapley.factor.{f_name}.usd",
                value=round(f_val, 4),
                unit="usd",
                provenance=Provenance.SIMULATED,
                source="exact_5_factor_shapley"
            ),
            contribution_share_pct=Quantity(
                id=f"shapley.factor.{f_name}.pct",
                value=round(share, 2),
                unit="percent",
                provenance=Provenance.SIMULATED,
                source="exact_5_factor_shapley"
            )
        )

    return ExplainReport(
        target=target,
        total_value_usd=Quantity(
            id=f"shapley.total.{target}",
            value=round(tot_val, 4),
            unit="usd",
            provenance=Provenance.SIMULATED,
            source="exact_5_factor_shapley"
        ),
        factors=factors_map,
        efficiency_residual=Quantity(
            id="shapley.efficiency_residual",
            value=round(raw_shapley["efficiency_residual"], 9),
            unit="residual_usd",
            provenance=Provenance.SIMULATED,
            source="exact_5_factor_shapley"
        ),
        is_efficient=raw_shapley["is_efficient"]
    )
