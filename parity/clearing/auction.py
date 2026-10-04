from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

@dataclass(frozen=True)
class AuctionBid:
    bid_id: str
    buyer_id: str
    archetype: str
    incumbent_model: str
    max_price_per_m: float
    quantity_m: float

@dataclass(frozen=True)
class AuctionAsk:
    ask_id: str
    seller_id: str
    model_offered: str
    min_price_per_m: float
    quantity_m: float

@dataclass
class MatchResult:
    bid_id: str
    ask_id: str
    matched_quantity_m: float
    clearing_price: float
    buyer_surplus: float
    seller_surplus: float

def clear_resale_market(
    bids: List[AuctionBid],
    asks: List[AuctionAsk],
    substitutability_matrix: Dict[str, Dict[str, Any]],
    use_substitutability: bool = True,
    platform_fee_rate: float = 0.0025
) -> Dict[str, Any]:
    remaining_asks = {a.ask_id: a.quantity_m for a in asks}
    ask_by_id = {a.ask_id: a for a in asks}
    sorted_bids = sorted(bids, key=lambda b: b.max_price_per_m, reverse=True)

    matches: List[MatchResult] = []
    total_welfare = 0.0

    for bid in sorted_bids:
        bid_rem = bid.quantity_m
        eligible_asks = []
        for a_id, rem_qty in remaining_asks.items():
            if rem_qty <= 0.0:
                continue
            ask = ask_by_id[a_id]
            if ask.min_price_per_m > bid.max_price_per_m:
                continue

            if not use_substitutability:
                if ask.model_offered == bid.incumbent_model:
                    eligible_asks.append(ask)
            else:
                arch_matrix = substitutability_matrix.get(bid.archetype, {})
                cand_info = arch_matrix.get(ask.model_offered, {})
                is_substitutable = (
                    ask.model_offered == bid.incumbent_model
                    or cand_info.get("decision") == "NON_INFERIOR"
                    or cand_info.get("p_non_inferior", 0.0) >= 0.85
                )
                if is_substitutable:
                    eligible_asks.append(ask)

        eligible_asks = sorted(eligible_asks, key=lambda a: a.min_price_per_m)
        for ask in eligible_asks:
            if bid_rem <= 0.0:
                break
            avail = remaining_asks[ask.ask_id]
            if avail <= 0.0:
                continue
            q_trade = min(bid_rem, avail)
            matches.append(MatchResult(
                bid_id=bid.bid_id,
                ask_id=ask.ask_id,
                matched_quantity_m=q_trade,
                clearing_price=0.0,
                buyer_surplus=0.0,
                seller_surplus=0.0
            ))

            remaining_asks[ask.ask_id] -= q_trade
            bid_rem -= q_trade

    if matches:
        matched_bid_prices = [next(b.max_price_per_m for b in bids if b.bid_id == m.bid_id) for m in matches]
        matched_ask_prices = [ask_by_id[m.ask_id].min_price_per_m for m in matches]
        min_b = min(matched_bid_prices)
        max_a = max(matched_ask_prices)
        if min_b >= max_a:
            uniform_p = 0.5 * (min_b + max_a)
        else:
            uniform_p = float(np.median(matched_bid_prices + matched_ask_prices))

        updated_matches = []
        for m in matches:
            b_val = next(b.max_price_per_m for b in bids if b.bid_id == m.bid_id)
            a_val = ask_by_id[m.ask_id].min_price_per_m
            p_trade = min(max(uniform_p, a_val), b_val)
            b_surplus = (b_val - p_trade) * m.matched_quantity_m
            s_surplus = (p_trade - a_val) * m.matched_quantity_m
            total_welfare += (b_surplus + s_surplus)
            updated_matches.append(MatchResult(
                bid_id=m.bid_id,
                ask_id=m.ask_id,
                matched_quantity_m=m.matched_quantity_m,
                clearing_price=round(p_trade, 4),
                buyer_surplus=round(b_surplus, 4),
                seller_surplus=round(s_surplus, 4)
            ))
        matches = updated_matches

    envy_free_count = 0
    for bid in bids:
        buyer_matches = [m for m in matches if m.bid_id == bid.bid_id]
        if not buyer_matches:
            envy_free_count += 1
            continue
        own_surplus = sum(m.buyer_surplus for m in buyer_matches) / sum(m.matched_quantity_m for m in buyer_matches)
        
        is_envy = False
        for other_m in matches:
            if other_m.bid_id != bid.bid_id:
                hypo_surplus = bid.max_price_per_m - other_m.clearing_price
                if hypo_surplus > (own_surplus + 1e-4):
                    is_envy = True
                    break
        if not is_envy:
            envy_free_count += 1

    envy_free_rate = float(envy_free_count / max(1, len(bids)))

    return {
        "matches": matches,
        "total_welfare": round(total_welfare, 4),
        "traded_volume_m": round(sum(m.matched_quantity_m for m in matches), 4),
        "envy_free_rate": round(envy_free_rate, 4),
        "num_matches": len(matches)
    }
