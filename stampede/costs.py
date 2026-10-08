import time
from typing import Dict, List, Any, Tuple, Optional
from pydantic import BaseModel
from stampede.settings import settings

class StageEstimate(BaseModel):
    stage: str
    expected_calls_lo: int
    expected_calls_hi: int
    expected_tokens_lo: int
    expected_tokens_hi: int
    expected_cost_usd_lo: float
    expected_cost_usd_hi: float

class RunEstimate(BaseModel):
    stages: List[StageEstimate]
    total_calls_lo: int
    total_calls_hi: int
    total_tokens_lo: int
    total_tokens_hi: int
    total_cost_usd_lo: float
    total_cost_usd_hi: float
    requires_confirmation: bool
    is_within_session_cap: bool
    is_within_daily_cap: bool
    remaining_session_budget_usd: float
    remaining_daily_budget_usd: float

    @property
    def total_estimated_usd(self) -> float:
        return self.total_cost_usd_hi

class CostLedger:
    def __init__(self, log_path: Optional[Any] = None) -> None:
        self.daily_spend_usd: float = 0.0
        self.last_reset_day: int = int(time.time() // 86400)
        self.byok_spend_usd: float = 0.0
        self.log_path = log_path
        self.session_spends: Dict[str, float] = {}

    def _check_day_rollover(self) -> None:
        current_day = int(time.time() // 86400)
        if current_day != self.last_reset_day:
            self.daily_spend_usd = 0.0
            self.last_reset_day = current_day

    def get_remaining_daily_budget(self) -> float:
        self._check_day_rollover()
        return max(0.0, settings.daily_cap_usd - self.daily_spend_usd)

    def record_spend(self, amount_usd: float, is_byok: bool = False, session_id: Optional[str] = None) -> None:
        self._check_day_rollover()
        if is_byok:
            self.byok_spend_usd += amount_usd
        else:
            self.daily_spend_usd += amount_usd
        if session_id:
            self.session_spends[session_id] = self.session_spends.get(session_id, 0.0) + amount_usd

    def check_and_allocate(self, session_id: str, amount_usd: float, is_byok: bool = False) -> Tuple[bool, float]:
        self._check_day_rollover()
        current_sess = self.session_spends.get(session_id, 0.0)
        if not is_byok and (current_sess + amount_usd > settings.session_cap_usd):
            return False, max(0.0, settings.session_cap_usd - current_sess)
        if not is_byok and (self.daily_spend_usd + amount_usd > settings.daily_cap_usd):
            return False, max(0.0, settings.daily_cap_usd - self.daily_spend_usd)
        return True, max(0.0, settings.session_cap_usd - current_sess - amount_usd)

    def record_call(self, session_id: str, call_name: str, model: str, in_tok: int, out_tok: int, cost_usd: float) -> None:
        self.session_spends[session_id] = self.session_spends.get(session_id, 0.0) + cost_usd
        self.record_spend(cost_usd, is_byok=False)
        if self.log_path:
            import json
            from pathlib import Path
            p = Path(self.log_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            entry = {"session_id": session_id, "call": call_name, "model": model, "cost_usd": cost_usd}
            with open(p, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

global_cost_ledger = CostLedger()

def estimate_run_cost(
    stages: List[str],
    num_prompts: int = 24,
    num_candidates: int = 2,
    session_spend_usd: float = 0.0,
    is_byok: bool = False,
    is_judged: bool = True
) -> RunEstimate:
    stage_estimates = []

    if "ingest" in stages:
        stage_estimates.append(
            StageEstimate(
                stage="ingest",
                expected_calls_lo=0,
                expected_calls_hi=1,
                expected_tokens_lo=0,
                expected_tokens_hi=1200,
                expected_cost_usd_lo=0.0,
                expected_cost_usd_hi=0.005
            )
        )

    if "parity" in stages:
        pairs = max(1, num_candidates)
        min_prompts_per_pair = min(num_prompts, 8)
        max_prompts_per_pair = min(num_prompts, 40)
        judges_mult = 4 if is_judged else 1
        lo_calls = pairs * min_prompts_per_pair * (2 if is_judged else 1)
        hi_calls = pairs * max_prompts_per_pair * (2 if is_judged else 1)
        if is_judged:
            lo_calls += pairs * min_prompts_per_pair * 2
            hi_calls += pairs * max_prompts_per_pair * 2
        lo_tokens = lo_calls * 400
        hi_tokens = hi_calls * 900
        lo_cost = lo_tokens * 0.000004
        hi_cost = hi_tokens * 0.000008
        stage_estimates.append(
            StageEstimate(
                stage="parity",
                expected_calls_lo=lo_calls,
                expected_calls_hi=hi_calls,
                expected_tokens_lo=lo_tokens,
                expected_tokens_hi=hi_tokens,
                expected_cost_usd_lo=round(lo_cost, 4),
                expected_cost_usd_hi=round(hi_cost, 4)
            )
        )

    if "narrative" in stages or "agent" in stages:
        stage_estimates.append(
            StageEstimate(
                stage="narrative",
                expected_calls_lo=1,
                expected_calls_hi=4,
                expected_tokens_lo=800,
                expected_tokens_hi=3500,
                expected_cost_usd_lo=0.005,
                expected_cost_usd_hi=0.035
            )
        )

    for st in ("forecast", "quotes", "valuation", "plan", "exit", "seller"):
        if st in stages:
            stage_estimates.append(
                StageEstimate(
                    stage=st,
                    expected_calls_lo=0,
                    expected_calls_hi=0,
                    expected_tokens_lo=0,
                    expected_tokens_hi=0,
                    expected_cost_usd_lo=0.0,
                    expected_cost_usd_hi=0.0
                )
            )

    tot_calls_lo = sum(s.expected_calls_lo for s in stage_estimates)
    tot_calls_hi = sum(s.expected_calls_hi for s in stage_estimates)
    tot_tok_lo = sum(s.expected_tokens_lo for s in stage_estimates)
    tot_tok_hi = sum(s.expected_tokens_hi for s in stage_estimates)
    tot_cost_lo = sum(s.expected_cost_usd_lo for s in stage_estimates)
    tot_cost_hi = sum(s.expected_cost_usd_hi for s in stage_estimates)

    rem_session = max(0.0, settings.session_cap_usd - session_spend_usd)
    rem_daily = global_cost_ledger.get_remaining_daily_budget() if not is_byok else 9999.0

    return RunEstimate(
        stages=stage_estimates,
        total_calls_lo=tot_calls_lo,
        total_calls_hi=tot_calls_hi,
        total_tokens_lo=tot_tok_lo,
        total_tokens_hi=tot_tok_hi,
        total_cost_usd_lo=round(tot_cost_lo, 4),
        total_cost_usd_hi=round(tot_cost_hi, 4),
        requires_confirmation=tot_cost_hi > settings.estimate_confirm_threshold_usd,
        is_within_session_cap=tot_cost_hi <= rem_session,
        is_within_daily_cap=tot_cost_hi <= rem_daily,
        remaining_session_budget_usd=round(rem_session, 4),
        remaining_daily_budget_usd=round(rem_daily, 4)
    )
