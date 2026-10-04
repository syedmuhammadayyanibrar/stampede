import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Any, Tuple
from .forecast import ForecastResult

@dataclass
class ContractRecommendation:
    optimal_notional_m: float
    naive_notional_m: float
    critical_ratio: float
    forward_strike_per_m: float
    expected_fwd_bill: float
    expected_spot_bill: float
    expected_savings: float
    savings_pct: float
    downside_p95_cost: float
    portfolio_mix: Dict[str, Any]
    crunch_exposure_penalty: float

def compute_optimal_contract_order(
    forecast: ForecastResult,
    spot_initial: float = 5.00,
    fair_fwd_price: float = 3.63,
    crunch_spread_pct: float = 0.358
) -> ContractRecommendation:
    d_scenarios = forecast.scenario_total_demands
    
    c_u = max(0.10, spot_initial - fair_fwd_price)
    c_o = max(0.10, fair_fwd_price * crunch_spread_pct)
    critical_ratio = c_u / (c_u + c_o)
    
    q_star = float(np.percentile(d_scenarios, critical_ratio * 100.0))
    q_naive = forecast.expected_total_demand_m
    
    def eval_cost(q_contract: float, shock_spread: float) -> Tuple[float, float]:
        consumed = np.minimum(d_scenarios, q_contract)
        surplus = np.maximum(0.0, q_contract - d_scenarios)
        shortfall = np.maximum(0.0, d_scenarios - q_contract)
        
        salvage_price = fair_fwd_price * (1.0 - shock_spread)
        net_costs = (q_contract * fair_fwd_price) - (surplus * salvage_price) + (shortfall * spot_initial)
        return float(np.mean(net_costs)), float(np.percentile(net_costs, 95.0))
    
    mean_cost_star, p95_cost_star = eval_cost(q_star, crunch_spread_pct)
    mean_cost_spot = float(np.mean(d_scenarios * spot_initial))
    
    savings = mean_cost_spot - mean_cost_star
    savings_pct = (savings / max(1e-4, mean_cost_spot)) * 100.0
    
    mean_cost_shock, _ = eval_cost(q_star, 0.45)
    mean_cost_normal, _ = eval_cost(q_star, 0.06)
    crunch_exposure = mean_cost_shock - mean_cost_normal
    
    portfolio_mix = {
        "strategy_name": "70/30 Protected Core",
        "specific_model_notional_m": round(q_star * 0.70, 1),
        "best_in_class_notional_m": round(q_star * 0.30, 1),
        "delivery_structure": "3x 30-Day Staggered Tranches",
        "protection_rationale": "30% best-in-class allocation eliminates replacement risk on core agent workloads, while staggered 30-day tenors prevent concentrated 90-day obsolescence exposure."
    }
    
    return ContractRecommendation(
        optimal_notional_m=round(q_star, 1),
        naive_notional_m=round(q_naive, 1),
        critical_ratio=round(critical_ratio, 3),
        forward_strike_per_m=round(fair_fwd_price, 3),
        expected_fwd_bill=round(mean_cost_star, 2),
        expected_spot_bill=round(mean_cost_spot, 2),
        expected_savings=round(savings, 2),
        savings_pct=round(savings_pct, 1),
        downside_p95_cost=round(p95_cost_star, 2),
        portfolio_mix=portfolio_mix,
        crunch_exposure_penalty=round(crunch_exposure, 2)
    )
