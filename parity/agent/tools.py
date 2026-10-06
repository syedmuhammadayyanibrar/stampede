import uuid
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class ToolExecutionRecord:
    def __init__(self) -> None:
        self.history: List[Dict[str, Any]] = []
        self.call_outputs: Dict[str, Any] = []

    def record(self, tool_name: str, args: Dict[str, Any], result: Dict[str, Any]) -> str:
        call_id = f"call_{uuid.uuid4().hex[:8]}"
        self.history.append({
            "tool_call_id": call_id,
            "tool_name": tool_name,
            "args": args,
            "result": result
        })
        return call_id

def tool_load_usage(csv_content: str) -> Dict[str, Any]:
    lines = [l.strip() for l in csv_content.strip().split("\n") if l.strip()]
    num_rows = max(0, len(lines) - 1)
    tot_tokens = num_rows * 1500000.0
    return {
        "num_days": num_rows,
        "total_tokens_m": round(tot_tokens / 1e6, 2),
        "mean_daily_tokens_m": round((tot_tokens / 1e6) / max(1, num_rows), 2)
    }

def tool_extract_plan(plan_text: str) -> Dict[str, Any]:
    multiplier = 1.25 if "+" in plan_text or "expand" in plan_text.lower() else 1.0
    return {
        "demand_multiplier": multiplier,
        "has_milestones": len(plan_text) > 10,
        "extracted_quote": plan_text[:40] if plan_text else ""
    }

def tool_forecast_usage(mean_daily_m: float, multiplier: float, horizon_days: int = 90) -> Dict[str, Any]:
    expected_tot = mean_daily_m * multiplier * horizon_days
    p10 = expected_tot * 0.85
    p90 = expected_tot * 1.20
    return {
        "horizon_days": horizon_days,
        "expected_total_m": round(expected_tot, 2),
        "p10_total_m": round(p10, 2),
        "p90_total_m": round(p90, 2)
    }

def tool_get_substitutability(archetype: str, candidate_model: str) -> Dict[str, Any]:
    is_non_inferior = "mini" in candidate_model or "chat" in candidate_model or "flash" in candidate_model
    p_non_inf = 0.94 if is_non_inferior else 0.45
    eff_cost = 0.55 if "mini" in candidate_model else (1.20 if "chat" in candidate_model else 4.50)
    return {
        "archetype": archetype,
        "candidate_model": candidate_model,
        "decision": "NON_INFERIOR" if is_non_inferior else "INCONCLUSIVE",
        "p_non_inferior": p_non_inf,
        "effective_cost_usd": eff_cost
    }

def tool_value_contract(spot_initial: float, tenor_days: int, discount_pct: float) -> Dict[str, Any]:
    strike = spot_initial * (1.0 - discount_pct)
    opt_val = spot_initial * 0.08
    d_min = 0.15
    return {
        "forward_strike": round(strike, 2),
        "resale_option_value": round(opt_val, 2),
        "minimum_required_discount": d_min,
        "expected_value_usd": round(strike + opt_val, 2)
    }

def tool_list_offers() -> List[Dict[str, Any]]:
    return [
        {"offer_id": "off_01", "model": "openai/gpt-4o-mini", "tenor_days": 90, "discount_pct": 0.20, "price_per_m": 0.40},
        {"offer_id": "off_02", "model": "deepseek/deepseek-chat", "tenor_days": 90, "discount_pct": 0.15, "price_per_m": 1.00},
        {"offer_id": "off_03", "model": "anthropic/claude-3.5-sonnet", "tenor_days": 90, "discount_pct": 0.12, "price_per_m": 3.50}
    ]

def tool_score_bids(bids: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    scored = []
    for b in bids:
        eff = b.get("price_per_m", 4.0) * 0.95
        scored.append({
            "bid_id": b.get("offer_id", "b1"),
            "effective_score": round(eff, 2),
            "is_recommended": eff < 2.0
        })
    return scored
