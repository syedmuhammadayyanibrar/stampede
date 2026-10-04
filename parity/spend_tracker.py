import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from parity.io import write_json_atomic, read_json

MODEL_PRICING_PER_M: Dict[str, Dict[str, float]] = {
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "anthropic/claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
    "anthropic/claude-3.5-haiku": {"input": 0.80, "output": 4.00},
    "google/gemini-2.0-flash-001": {"input": 0.10, "output": 0.40},
    "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28}
}

class SpendTracker:
    def __init__(
        self,
        budget_usd_cap: float = 50.00,
        sub_cap_ceiling_usd: float = 4.00,
        ledger_path: Path = Path("data/parity/spend_ledger.json")
    ) -> None:
        self.budget_usd_cap = budget_usd_cap
        self.sub_cap_ceiling_usd = sub_cap_ceiling_usd
        self.ledger_path = ledger_path
        self._ensure_ledger()

    def _ensure_ledger(self) -> None:
        if not self.ledger_path.exists():
            init_data = {
                "budget_usd_cap": self.budget_usd_cap,
                "sub_cap_ceiling_usd": self.sub_cap_ceiling_usd,
                "cumulative_spend_usd": 0.0,
                "records": []
            }
            write_json_atomic(self.ledger_path, init_data)

    def get_cumulative_spend(self) -> float:
        data = read_json(self.ledger_path)
        return float(data.get("cumulative_spend_usd", 0.0))

    def estimate_call_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = MODEL_PRICING_PER_M.get(model, {"input": 2.50, "output": 10.00})
        cost = (prompt_tokens * pricing["input"] / 1000000.0) + (completion_tokens * pricing["output"] / 1000000.0)
        return float(cost)

    def record_call_spend(
        self,
        call_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        is_ceiling_check: bool = False
    ) -> float:
        call_cost = self.estimate_call_cost(model, prompt_tokens, completion_tokens)
        data = read_json(self.ledger_path)
        current_spend = float(data.get("cumulative_spend_usd", 0.0))
        new_spend = current_spend + call_cost

        if is_ceiling_check and new_spend > self.sub_cap_ceiling_usd:
            raise RuntimeError(f"CEILING_CHECK_SUBCAP_EXCEEDED: Ceiling spend {new_spend:.4f} exceeds sub-cap {self.sub_cap_ceiling_usd:.2f}")

        if new_spend > self.budget_usd_cap:
            raise RuntimeError(f"PARITY_BUDGET_EXCEEDED: Requested spend {new_spend:.4f} exceeds cap {self.budget_usd_cap:.2f}")

        data["cumulative_spend_usd"] = round(new_spend, 6)
        data["records"].append({
            "call_id": call_id,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": round(call_cost, 6),
            "total_after_usd": round(new_spend, 6),
            "is_ceiling_check": is_ceiling_check
        })
        write_json_atomic(self.ledger_path, data)
        return call_cost
