from typing import Dict, List, Tuple, Any, Optional

def compute_buyer_valuation(
    expected_gross_value: float,
    variance_gross_value: float,
    risk_aversion: float
) -> float:
    risk_penalty = 0.5 * risk_aversion * variance_gross_value
    return float(expected_gross_value - risk_penalty)

def compute_seller_reservation_cost(
    expected_unit_cost: float,
    variance_unit_cost: float,
    risk_aversion: float
) -> float:
    risk_premium = 0.5 * risk_aversion * variance_unit_cost
    return float(expected_unit_cost + risk_premium)

def evaluate_zopa_interval(
    buyer_valuation: float,
    seller_cost: float
) -> Dict[str, Any]:
    has_zopa = buyer_valuation >= seller_cost
    width = max(0.0, buyer_valuation - seller_cost)
    interval = [round(seller_cost, 4), round(buyer_valuation, 4)] if has_zopa else []
    return {
        "has_zopa": has_zopa,
        "zopa_width": round(width, 4),
        "zopa_interval": interval
    }

def evaluate_zopa_width_contraction(
    expected_value: float = 4.20,
    variance_value: float = 0.80,
    seller_cost: float = 2.50,
    risk_aversions: Optional[List[float]] = None
) -> Dict[str, Any]:
    rhos = risk_aversions or [0.0, 0.1, 0.25, 0.50]
    widths = []
    valuations = []

    for rho in rhos:
        v_b = compute_buyer_valuation(expected_value, variance_value, rho)
        zopa_res = evaluate_zopa_interval(v_b, seller_cost)
        widths.append(zopa_res["zopa_width"])
        valuations.append(round(v_b, 4))

    is_monotonically_contracting = True
    for i in range(len(widths) - 1):
        if widths[i] < widths[i + 1]:
            is_monotonically_contracting = False
            break

    return {
        "risk_aversions": rhos,
        "buyer_valuations": valuations,
        "zopa_widths": widths,
        "is_monotonically_contracting": is_monotonically_contracting
    }
