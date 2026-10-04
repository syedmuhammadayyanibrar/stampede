import numpy as np
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class RFQSimulationResult:
    notional_millions: float
    num_dealers: int
    normal_open_book_spread: float
    normal_rfq_best_spread: float
    normal_rfq_price_improvement_pct: float
    shock_open_book_spread: float
    shock_rfq_best_spread: float
    shock_rfq_price_improvement_pct: float
    rfq_dealer_bids_normal: List[float]
    rfq_dealer_bids_shock: List[float]

def simulate_rfq_flow(
    notional_millions: float = 500.0,
    num_dealers: int = 5,
    random_seed: int = 42
) -> RFQSimulationResult:
    rng = np.random.default_rng(random_seed)
    
    size_impact = min(0.08, (notional_millions / 100.0) * 0.012)
    norm_book_spread = 0.060 + size_impact
    shock_book_spread = 0.380 + (size_impact * 2.5)
    
    norm_dealer_quotes = []
    for i in range(num_dealers):
        dealer_inv_capacity = rng.uniform(0.6, 1.4)
        dealer_half_spread = 0.045 + (0.025 / dealer_inv_capacity)
        norm_dealer_quotes.append(float(dealer_half_spread))
    
    best_norm_rfq_spread = min(norm_dealer_quotes)
    norm_price_improvement = ((norm_book_spread - best_norm_rfq_spread) / norm_book_spread) * 100.0
    
    shock_dealer_quotes = []
    for i in range(num_dealers):
        dealer_toxic_aversion = rng.uniform(1.2, 2.2)
        dealer_shock_spread = 0.30 + (0.08 * dealer_toxic_aversion)
        shock_dealer_quotes.append(float(dealer_shock_spread))
    
    best_shock_rfq_spread = min(shock_dealer_quotes)
    shock_price_improvement = ((shock_book_spread - best_shock_rfq_spread) / shock_book_spread) * 100.0
    
    return RFQSimulationResult(
        notional_millions=notional_millions,
        num_dealers=num_dealers,
        normal_open_book_spread=norm_book_spread,
        normal_rfq_best_spread=best_norm_rfq_spread,
        normal_rfq_price_improvement_pct=norm_price_improvement,
        shock_open_book_spread=shock_book_spread,
        shock_rfq_best_spread=best_shock_rfq_spread,
        shock_rfq_price_improvement_pct=shock_price_improvement,
        rfq_dealer_bids_normal=[round(q, 4) for q in norm_dealer_quotes],
        rfq_dealer_bids_shock=[round(q, 4) for q in shock_dealer_quotes]
    )
