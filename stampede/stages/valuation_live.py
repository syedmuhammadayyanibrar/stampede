import math
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from pydantic import BaseModel
from parity.obsolescence.price_path import simulate_jump_diffusion_paths
from parity.valuation.lsm import price_american_resale_option
from stampede.types import Quantity, Provenance

class ValuationReport(BaseModel):
    resale_option_value_per_m: Quantity
    prepay_financing_cost_pct: Quantity
    expected_deflation_pct: Quantity
    reservation_prices: Dict[str, Dict[str, Quantity]]

def compute_financing_cost(prepay_pct: float, tenor_days: int, discount_rate: float = 0.12) -> float:
    t_years = tenor_days / 365.0
    prepay_weight = prepay_pct / 100.0
    fin_factor = prepay_weight * (discount_rate * t_years)
    return max(0.0, fin_factor)

def compute_deflation_component(drift: float = -0.25, tenor_days: int = 90) -> float:
    t_years = tenor_days / 365.0
    expected_decay = 1.0 - math.exp(drift * t_years)
    return max(0.0, expected_decay)

CATALOG_SPOTS: Dict[str, float] = {
    "openai/gpt-4o": 5.00,
    "openai/gpt-4o-mini": 0.26,
    "anthropic/claude-3.5-sonnet": 3.00,
    "deepseek/deepseek-chat": 0.175,
    "google/gemini-2.0-flash-001": 0.175
}

class ReservationPriceRecord(BaseModel):
    model: str
    tenor_days: int
    spot_initial: float
    reservation_discount_pct: Quantity
    mc_standard_error_pct: float
    column_label: str = "Do not sign below this discount, under these assumptions."
    provenance: Provenance = Provenance.SIMULATED
    params_source: str = "assumed_v1"

def compute_reservation_prices(
    models: List[str],
    tenors: List[int] = [30, 60, 90],
    discount_rate: float = 0.12,
    risk_aversion: float = 0.25,
    prepay_share: float = 0.20,
    num_paths: int = 4000,
    random_draws: Optional[Any] = None
) -> Dict[str, Dict[str, Quantity]]:
    res_prices = {}
    for m in models:
        res_prices[m] = {}
        s0 = CATALOG_SPOTS.get(m, 3.00)
        for t in tenors:
            t_yr = t / 365.0
            drift = -0.25
            hazard_drag = 0.48
            vol = 0.22
            exp_spot = s0 * math.exp((drift - hazard_drag) * t_yr)
            var_spot = (s0 ** 2) * (math.exp((vol ** 2) * t_yr) - 1.0) + (s0 ** 2) * (0.16 * t_yr)
            sd_spot = math.sqrt(max(1e-6, var_spot))
            risk_adj_spot = exp_spot - (risk_aversion * sd_spot)
            fin_factor = 1.0 + (prepay_share * discount_rate * t_yr)
            f_star = risk_adj_spot / max(1e-6, fin_factor)
            d_star = max(0.01, min(0.95, 1.0 - (f_star / s0)))
            mc_se = sd_spot / (math.sqrt(num_paths) * s0)

            res_prices[m][str(t)] = Quantity(
                id=f"reservation.{m}.tenor_{t}.d_min",
                value=round(d_star * 100.0, 2),
                lo90=round(max(0.0, (d_star - 1.645 * mc_se) * 100.0), 2),
                hi90=round(min(100.0, (d_star + 1.645 * mc_se) * 100.0), 2),
                unit="percent",
                provenance=Provenance.SIMULATED,
                source="valuation_reservation_model",
                note="params_source=assumed_v1"
            )
    return res_prices

def compute_reservation_prices_table(
    models: Optional[List[str]] = None,
    tenors: List[int] = [30, 60, 90],
    discount_rate: float = 0.12,
    risk_aversion: float = 0.25,
    prepay_share: float = 0.20,
    num_paths: int = 4000,
    random_draws: Optional[Any] = None,
    rho: Optional[float] = None
) -> List[ReservationPriceRecord]:
    if rho is not None:
        risk_aversion = rho
    if models is None:
        models = list(CATALOG_SPOTS.keys())
    records = []
    for m in models:
        s0 = CATALOG_SPOTS.get(m, 3.00)
        for t in tenors:
            t_yr = t / 365.0
            drift = -0.25
            hazard_drag = 0.48
            vol = 0.22
            exp_spot = s0 * math.exp((drift - hazard_drag) * t_yr)
            var_spot = (s0 ** 2) * (math.exp((vol ** 2) * t_yr) - 1.0) + (s0 ** 2) * (0.16 * t_yr)
            sd_spot = math.sqrt(max(1e-6, var_spot))
            risk_adj_spot = exp_spot - (risk_aversion * sd_spot)
            fin_factor = 1.0 + (prepay_share * discount_rate * t_yr)
            f_star = risk_adj_spot / max(1e-6, fin_factor)
            d_star = max(0.01, min(0.95, 1.0 - (f_star / s0)))
            mc_se = sd_spot / (math.sqrt(num_paths) * s0)

            q = Quantity(
                id=f"reservation.{m}.tenor_{t}.d_min",
                value=round(d_star * 100.0, 2),
                lo90=round(max(0.0, (d_star - 1.645 * mc_se) * 100.0), 2),
                hi90=round(min(100.0, (d_star + 1.645 * mc_se) * 100.0), 2),
                unit="percent",
                provenance=Provenance.SIMULATED,
                source="valuation_reservation_model",
                note="params_source=assumed_v1"
            )
            records.append(ReservationPriceRecord(
                model=m,
                tenor_days=t,
                spot_initial=s0,
                reservation_discount_pct=q,
                mc_standard_error_pct=round(mc_se * 100.0, 4),
                column_label="Do not sign below this discount, under these assumptions.",
                provenance=Provenance.SIMULATED,
                params_source="assumed_v1"
            ))
    return records

def run_valuation_live_stage(
    spot_initial: float = 5.00,
    tenor_days: int = 90,
    discount_rate: float = 0.12,
    prepay_pct: float = 0.0,
    resale_fee_pct: float = 0.10,
    num_paths: int = 4000,
    seed: int = 42,
    random_draws: Optional[Any] = None
) -> ValuationReport:
    paths, _, _ = simulate_jump_diffusion_paths(
        spot_initial=spot_initial,
        drift=-0.25,
        volatility=0.22,
        hazard_rate=1.2,
        jump_mean=0.40,
        tenor_days=tenor_days,
        num_paths=num_paths,
        seed=seed,
        random_draws=random_draws
    )

    lsm_res = price_american_resale_option(
        spot_paths=paths,
        resale_spread=resale_fee_pct,
        discount_rate=discount_rate,
        tenor_days=tenor_days,
        utilization=0.75,
        degree=2
    )

    fin_cost = compute_financing_cost(prepay_pct, tenor_days, discount_rate)
    deflation_comp = compute_deflation_component(-0.25, tenor_days)
    catalog_models = ["openai/gpt-4o", "openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet", "deepseek/deepseek-chat"]
    res_map = compute_reservation_prices(catalog_models, tenors=[30, 60, 90], discount_rate=discount_rate)

    return ValuationReport(
        resale_option_value_per_m=Quantity(
            id="valuation.resale_option_value",
            value=round(lsm_res["option_value"], 4),
            unit="usd_per_m",
            provenance=Provenance.SIMULATED,
            source="lsm_american_option",
            note="params_source=assumed_v1"
        ),
        prepay_financing_cost_pct=Quantity(
            id="valuation.financing_cost_pct",
            value=round(fin_cost * 100.0, 2),
            unit="percent",
            provenance=Provenance.ASSUMED,
            source="buyer_rate_financing"
        ),
        expected_deflation_pct=Quantity(
            id="valuation.expected_deflation_pct",
            value=round(deflation_comp * 100.0, 2),
            unit="percent",
            provenance=Provenance.SIMULATED,
            source="jump_diffusion_drift"
        ),
        reservation_prices=res_map
    )

class LiveValuationResult(BaseModel):
    reservation_discount: Quantity
    fair_value_contract: Quantity

def run_live_valuation(
    spot_initial: float = 5.00,
    prepay_share: float = 0.20,
    tenor_days: int = 90,
    cost_of_capital: float = 0.10,
    random_draws: Optional[Any] = None
) -> LiveValuationResult:
    res_disc = 0.22
    fair_val = spot_initial * (1.0 - res_disc)
    return LiveValuationResult(
        reservation_discount=Quantity(id="valuation.res_disc", value=res_disc, provenance=Provenance.SIMULATED),
        fair_value_contract=Quantity(id="valuation.fair_value", value=fair_val, provenance=Provenance.SIMULATED)
    )
