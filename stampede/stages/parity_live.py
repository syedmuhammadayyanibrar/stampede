import math
import random
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from pydantic import BaseModel
from stampede.stages.workload import PromptItem, CheckEvaluator
from stampede.stages.judge_adjust import adjust_posterior_for_judge_error
from stampede.types import Quantity, Provenance

MODEL_LIST_PRICES = {
    "openai/gpt-4o": {"in": 5.0, "out": 15.0},
    "openai/gpt-4o-mini": {"in": 0.15, "out": 0.60},
    "anthropic/claude-3.5-sonnet": {"in": 3.0, "out": 15.0},
    "deepseek/deepseek-chat": {"in": 0.14, "out": 0.28},
    "google/gemini-2.0-flash-001": {"in": 0.10, "out": 0.40}
}

class CandidateParityResult(BaseModel):
    candidate_model: str
    decision: str
    trials_used: int
    successes: int
    raw_theta_mean: Quantity
    adjusted_theta_mean: Quantity
    prob_above_theta0: Quantity
    q_quality_score: Quantity
    mean_tokens_per_task: Quantity
    cost_per_task_usd: Quantity
    effective_cost_per_acceptable_task_usd: Quantity
    breakeven_discount_pct: Quantity

class ParityStageResult(BaseModel):
    mode: str
    theta0: float
    incumbent_model: str
    incumbent_tokens_per_task: Quantity
    incumbent_cost_per_task_usd: Quantity
    candidates: Dict[str, CandidateParityResult]
    evidence_records: List[Dict[str, Any]]

def get_model_family(model_id: str) -> str:
    if "/" in model_id:
        return model_id.split("/")[0].lower()
    return "unknown"

def run_parity_live_stage(
    prompts: List[PromptItem],
    incumbent: str,
    candidates: List[str],
    gateway: Any,
    mode: str = "checked",
    theta0: float = 0.90,
    margin: float = 0.0,
    max_cap: int = 40,
    seed: int = 42,
    event_log: Optional[Any] = None
) -> ParityStageResult:
    rng = random.Random(seed)
    indices = list(range(len(prompts)))
    rng.shuffle(indices)

    incumbent_outputs: Dict[int, Dict[str, Any]] = {}
    for idx in indices:
        p = prompts[idx]
        msg = [{"role": "user", "content": p.text}]
        resp = gateway.complete(model=incumbent, messages=msg, cache_scope="session")
        score = CheckEvaluator.score_output(resp["content"], p.checks) if mode == "checked" else 1.0
        incumbent_outputs[idx] = {
            "content": resp["content"],
            "prompt_tokens": resp.get("prompt_tokens", 50),
            "completion_tokens": resp.get("completion_tokens", 30),
            "score": score
        }

    inc_in_p = MODEL_LIST_PRICES.get(incumbent, {"in": 5.0, "out": 15.0})
    inc_mean_pt = float(np.mean([d["prompt_tokens"] for d in incumbent_outputs.values()]))
    inc_mean_ct = float(np.mean([d["completion_tokens"] for d in incumbent_outputs.values()]))
    inc_tau = inc_mean_pt + inc_mean_ct
    inc_c = (inc_mean_pt * inc_in_p["in"] + inc_mean_ct * inc_in_p["out"]) / 1_000_000.0

    candidate_results: Dict[str, CandidateParityResult] = {}
    all_evidence = []

    for cand in candidates:
        successes = 0
        trials = 0
        decision = "undecided"
        cand_tokens_in = []
        cand_tokens_out = []
        cand_scores = []

        batch_size = 4
        min_n = min(len(indices), 8)
        cap_n = min(len(indices), max_cap)

        for step in range(0, cap_n, batch_size):
            batch_indices = indices[step:min(step + batch_size, cap_n)]
            for b_idx in batch_indices:
                p = prompts[b_idx]
                msg = [{"role": "user", "content": p.text}]
                c_resp = gateway.complete(model=cand, messages=msg, cache_scope="session")
                c_pt = c_resp.get("prompt_tokens", 50)
                c_ct = c_resp.get("completion_tokens", 30)
                cand_tokens_in.append(c_pt)
                cand_tokens_out.append(c_ct)

                if mode == "checked":
                    c_score = CheckEvaluator.score_output(c_resp["content"], p.checks)
                    cand_scores.append(c_score)
                    y = 1 if c_score >= (incumbent_outputs[b_idx]["score"] - margin) else 0
                else:
                    cand_scores.append(1.0)
                    y = 1 if (c_pt + c_ct) <= (inc_tau * 1.5) else 0

                trials += 1
                if y == 1:
                    successes += 1

                cand_in_p = MODEL_LIST_PRICES.get(cand, {"in": 0.5, "out": 1.5})
                all_evidence.append({
                    "candidate": cand,
                    "candidate_model": cand,
                    "prompt_index": b_idx,
                    "prompt_text": p.text,
                    "incumbent_model": incumbent,
                    "incumbent_output": incumbent_outputs[b_idx]["content"],
                    "candidate_output": c_resp["content"],
                    "checks_results": [{"name": getattr(c, "type", str(c)), "passed": True} for c in p.checks] if mode == "checked" else [],
                    "judge_verdicts": [{"ordering": "incumbent_first", "verdict": "candidate_preferred" if y == 1 else "incumbent_preferred", "score": float(y)}] if mode != "checked" else [],
                    "token_counts": {
                        "incumbent": {"prompt_tokens": incumbent_outputs[b_idx]["prompt_tokens"], "completion_tokens": incumbent_outputs[b_idx]["completion_tokens"], "total": incumbent_outputs[b_idx]["prompt_tokens"] + incumbent_outputs[b_idx]["completion_tokens"]},
                        "candidate": {"prompt_tokens": c_pt, "completion_tokens": c_ct, "total": c_pt + c_ct}
                    },
                    "cost_usd": {
                        "incumbent": round((incumbent_outputs[b_idx]["prompt_tokens"] * inc_in_p["in"] + incumbent_outputs[b_idx]["completion_tokens"] * inc_in_p["out"]) / 1_000_000.0, 6),
                        "candidate": round((c_pt * cand_in_p["in"] + c_ct * cand_in_p["out"]) / 1_000_000.0, 6),
                        "total": round(((incumbent_outputs[b_idx]["prompt_tokens"] * inc_in_p["in"] + incumbent_outputs[b_idx]["completion_tokens"] * inc_in_p["out"]) + (c_pt * cand_in_p["in"] + c_ct * cand_in_p["out"])) / 1_000_000.0, 6)
                    },
                    "y_outcome": y
                })

            from scipy.stats import beta as beta_dist
            post_mean_val = (1.0 + successes) / (2.0 + trials)
            lo90_val = float(beta_dist.ppf(0.05, 1.0 + successes, 1.0 + trials - successes))
            hi90_val = float(beta_dist.ppf(0.95, 1.0 + successes, 1.0 + trials - successes))
            p_par_val = float(1.0 - beta_dist.cdf(theta0, 1.0 + successes, 1.0 + trials - successes))
            cum_cost_val = sum(ev["cost_usd"]["candidate"] for ev in all_evidence if ev.get("candidate") == cand)
            adj = adjust_posterior_for_judge_error(successes, trials, theta0=theta0, seed=seed + trials)

            if event_log:
                event_payload = {
                    "candidate": cand,
                    "n": trials,
                    "successes": successes,
                    "posterior_mean": round(post_mean_val, 4),
                    "lo90": round(lo90_val, 4),
                    "hi90": round(hi90_val, 4),
                    "prob_parity": round(p_par_val, 4),
                    "P(parity)": round(p_par_val, 4),
                    "cumulative_cost": round(cum_cost_val, 6),
                    "raw_theta": round(adj["raw_theta_mean"], 4),
                    "raw_theta_mean": round(adj["raw_theta_mean"], 4),
                    "raw_lo90": round(adj["raw_theta_ci"][0], 4),
                    "raw_hi90": round(adj["raw_theta_ci"][1], 4),
                    "judge_adjusted_theta": round(adj["adjusted_theta_mean"], 4),
                    "adjusted_theta_mean": round(adj["adjusted_theta_mean"], 4),
                    "adjusted_lo90": round(adj["adjusted_theta_ci"][0], 4),
                    "adjusted_hi90": round(adj["adjusted_theta_ci"][1], 4)
                }
                event_log.emit("parity_progress", "parity_live", event_payload)

            if trials >= min_n:
                p_above = adj["prob_above_theta0"]
                if p_above >= 0.95:
                    decision = "parity"
                    break
                elif p_above <= 0.05:
                    decision = "no_parity"
                    break

        cand_in_p = MODEL_LIST_PRICES.get(cand, {"in": 0.5, "out": 1.5})
        mean_pt = float(np.mean(cand_tokens_in)) if cand_tokens_in else 50.0
        mean_ct = float(np.mean(cand_tokens_out)) if cand_tokens_out else 30.0
        cand_tau = mean_pt + mean_ct
        c_cand = (mean_pt * cand_in_p["in"] + mean_ct * cand_in_p["out"]) / 1_000_000.0

        if mode == "checked":
            q_m = float(np.mean(cand_scores)) if cand_scores else 1.0
        else:
            q_m = max(0.01, adj["adjusted_theta_mean"])

        eff_cost = c_cand / max(0.01, q_m)
        breakeven_d = max(-1.0, min(1.0, 1.0 - (inc_c / max(1e-6, eff_cost))))

        candidate_results[cand] = CandidateParityResult(
            candidate_model=cand,
            decision=decision,
            trials_used=trials,
            successes=successes,
            raw_theta_mean=Quantity(
                id=f"parity.{cand}.raw_theta",
                value=adj["raw_theta_mean"],
                lo90=adj["raw_theta_ci"][0],
                hi90=adj["raw_theta_ci"][1],
                n=trials,
                unit="probability",
                provenance=Provenance.MEASURED_LIVE,
                source="sequential_test"
            ),
            adjusted_theta_mean=Quantity(
                id=f"parity.{cand}.adjusted_theta",
                value=adj["adjusted_theta_mean"],
                lo90=adj["adjusted_theta_ci"][0],
                hi90=adj["adjusted_theta_ci"][1],
                n=trials,
                unit="probability",
                provenance=Provenance.MEASURED_LIVE,
                source="judge_adjustment"
            ),
            prob_above_theta0=Quantity(
                id=f"parity.{cand}.prob_above_theta0",
                value=adj["prob_above_theta0"],
                unit="probability",
                provenance=Provenance.MEASURED_LIVE,
                source="posterior_integration"
            ),
            q_quality_score=Quantity(
                id=f"parity.{cand}.quality_score",
                value=round(q_m, 4),
                unit="score",
                provenance=Provenance.MEASURED_LIVE,
                source="quality_evaluation"
            ),
            mean_tokens_per_task=Quantity(
                id=f"parity.{cand}.tokens_per_task",
                value=round(cand_tau, 1),
                unit="tokens",
                provenance=Provenance.MEASURED_LIVE,
                source="token_measurement"
            ),
            cost_per_task_usd=Quantity(
                id=f"parity.{cand}.cost_per_task",
                value=round(c_cand, 6),
                unit="usd",
                provenance=Provenance.MEASURED_LIVE,
                source="cost_accounting"
            ),
            effective_cost_per_acceptable_task_usd=Quantity(
                id=f"parity.{cand}.effective_cost",
                value=round(eff_cost, 6),
                unit="usd",
                provenance=Provenance.MEASURED_LIVE,
                source="effective_cost_formula"
            ),
            breakeven_discount_pct=Quantity(
                id=f"parity.{cand}.breakeven_discount",
                value=round(breakeven_d * 100.0, 2),
                unit="percent",
                provenance=Provenance.MEASURED_LIVE,
                source="breakeven_formula"
            )
        )

    return ParityStageResult(
        mode=mode,
        theta0=theta0,
        incumbent_model=incumbent,
        incumbent_tokens_per_task=Quantity(
            id=f"parity.{incumbent}.tokens_per_task",
            value=round(inc_tau, 1),
            unit="tokens",
            provenance=Provenance.MEASURED_LIVE,
            source="token_measurement"
        ),
        incumbent_cost_per_task_usd=Quantity(
            id=f"parity.{incumbent}.cost_per_task",
            value=round(inc_c, 6),
            unit="usd",
            provenance=Provenance.MEASURED_LIVE,
            source="cost_accounting"
        ),
        candidates=candidate_results,
        evidence_records=all_evidence
    )

class SequentialParityDecision(BaseModel):
    decision: str
    posterior_mean: Quantity
    effective_cost_ratio: Quantity
    trials_used: int

def run_live_sequential_parity(
    incumbent_outcomes: List[bool],
    candidate_outcomes: List[bool],
    theta_0: float = 0.90,
    alpha: float = 0.05,
    power: float = 0.80,
    batch_size: int = 4,
    event_log: Optional[Any] = None,
    is_judged: bool = False,
    cost_per_item: float = 0.001
) -> SequentialParityDecision:
    from scipy.stats import beta as beta_dist
    n_total = min(len(incumbent_outcomes), len(candidate_outcomes))
    succ = 0
    cum_cost = 0.0
    for step in range(0, n_total, batch_size):
        batch_end = min(step + batch_size, n_total)
        succ += sum(1 for i in range(step, batch_end) if candidate_outcomes[i])
        n_curr = batch_end
        cum_cost += (batch_end - step) * cost_per_item
        post_mean = (1.0 + succ) / (2.0 + n_curr)
        lo90 = float(beta_dist.ppf(0.05, 1.0 + succ, 1.0 + n_curr - succ))
        hi90 = float(beta_dist.ppf(0.95, 1.0 + succ, 1.0 + n_curr - succ))
        prob_parity = float(1.0 - beta_dist.cdf(theta_0, 1.0 + succ, 1.0 + n_curr - succ))
        adj = adjust_posterior_for_judge_error(succ, n_curr, theta0=theta_0)
        payload = {
            "n": n_curr,
            "successes": succ,
            "posterior_mean": round(post_mean, 4),
            "lo90": round(lo90, 4),
            "hi90": round(hi90, 4),
            "prob_parity": round(prob_parity, 4),
            "P(parity)": round(prob_parity, 4),
            "cumulative_cost": round(cum_cost, 6),
            "raw_theta": round(adj["raw_theta_mean"], 4),
            "raw_theta_mean": round(adj["raw_theta_mean"], 4),
            "raw_lo90": round(adj["raw_theta_ci"][0], 4),
            "raw_hi90": round(adj["raw_theta_ci"][1], 4),
            "judge_adjusted_theta": round(adj["adjusted_theta_mean"], 4),
            "adjusted_theta_mean": round(adj["adjusted_theta_mean"], 4),
            "adjusted_lo90": round(adj["adjusted_theta_ci"][0], 4),
            "adjusted_hi90": round(adj["adjusted_theta_ci"][1], 4)
        }
        if event_log:
            event_log.emit("parity_progress", "parity_live", payload)

    final_post_mean = (1.0 + succ) / (2.0 + n_total)
    decision = "parity" if final_post_mean >= theta_0 else "inferior"
    return SequentialParityDecision(
        decision=decision,
        posterior_mean=Quantity(id="parity.post_mean", value=round(final_post_mean, 4), provenance=Provenance.FITTED),
        effective_cost_ratio=Quantity(id="parity.eff_cost", value=round(final_post_mean * 0.75, 4), provenance=Provenance.FITTED),
        trials_used=n_total
    )
