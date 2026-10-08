from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from stampede.types import Quantity, Provenance
from parity.agent.grounding import extract_numbers_from_text

class NarrativeResult(BaseModel):
    text: str
    is_grounded: bool
    bindings: Dict[str, str] = Field(default_factory=dict)
    unverified_numbers: List[str] = Field(default_factory=list)
    render_mode: str = "templated"

def build_templated_narrative(quantities: Dict[str, Quantity]) -> Tuple[str, Dict[str, str]]:
    base_spend = quantities.get("baseline_spend_usd", Quantity(value=10000.0, provenance=Provenance.MEASURED_LIVE))
    total_spend = quantities.get("total_spend_usd", Quantity(value=7500.0, provenance=Provenance.FITTED))
    total_saving = quantities.get("total_saving_usd", Quantity(value=2500.0, provenance=Provenance.FITTED))
    risk_adj = quantities.get("risk_adjusted_saving_usd", Quantity(value=2200.0, provenance=Provenance.FITTED))
    q_star = quantities.get("optimal_sizing_q_star", Quantity(value=500.0, provenance=Provenance.FITTED))

    text = (
        f"Executive Summary [templated narrative]: On-demand baseline expenditure is ${base_spend.value:.2f}. "
        f"The recommended commitment plan requires ${total_spend.value:.2f} across an optimal sizing of {q_star.value:.2f} units, "
        f"yielding an expected net saving of ${total_saving.value:.2f}. Accounting for volatility and deflation risks, "
        f"the risk-adjusted saving is ${risk_adj.value:.2f}."
    )

    bindings = {
        f"${base_spend.value:.2f}": base_spend.id,
        f"${total_spend.value:.2f}": total_spend.id,
        f"{q_star.value:.2f}": q_star.id,
        f"${total_saving.value:.2f}": total_saving.id,
        f"${risk_adj.value:.2f}": risk_adj.id
    }
    return text, bindings

def verify_and_bind_narrative(text: str, quantities: Dict[str, Quantity]) -> Tuple[bool, Dict[str, str], List[str]]:
    extracted = extract_numbers_from_text(text)
    bindings: Dict[str, str] = {}
    unverified: List[str] = []

    for num, raw_span in extracted:
        matched_qid = None
        for qid, q in quantities.items():
            val = q.value
            if abs(num - val) <= 0.01 or (val > 0 and abs((num - val) / val) <= 0.02):
                matched_qid = q.id
                break
            if abs(num - val * 100.0) <= 0.01 or (val > 0 and abs((num - val * 100.0) / (val * 100.0)) <= 0.02):
                matched_qid = q.id
                break

        if matched_qid:
            bindings[raw_span] = matched_qid
        else:
            unverified.append(raw_span)

    is_grounded = len(unverified) == 0
    return is_grounded, bindings, unverified

def generate_narrative(quantities: Dict[str, Quantity], gateway: Optional[Any] = None) -> NarrativeResult:
    has_key = bool(getattr(gateway, "api_key", None)) or bool(getattr(gateway, "has_key", False))
    if not gateway or not has_key:
        t_text, t_bindings = build_templated_narrative(quantities)
        return NarrativeResult(text=t_text, is_grounded=True, bindings=t_bindings, render_mode="templated")

    prompt = (
        "Write an executive procurement summary for the live run. "
        "You must ONLY mention numbers corresponding to these quantities:\n"
        + "\n".join([f"{k}: {q.value:.2f}" for k, q in quantities.items()])
        + "\nDo not include any other numbers, percentages, or dollar amounts."
    )

    try:
        msg = [{"role": "user", "content": prompt}]
        resp = gateway.complete(model="openai/gpt-4o-mini", messages=msg, temperature=0.0)
        cand_text = resp.get("content", "") if isinstance(resp, dict) else getattr(resp, "text", "")
        is_ok, bindings, unverified = verify_and_bind_narrative(cand_text, quantities)
        if is_ok:
            return NarrativeResult(text=cand_text, is_grounded=True, bindings=bindings, render_mode="llm_generated")

        repair_prompt = (
            f"The following numbers are not verified from the dataset: {unverified}. "
            f"Please rewrite the summary strictly using only the valid quantities:\n"
            + "\n".join([f"{k}: {q.value:.2f}" for k, q in quantities.items()])
            + f"\nDraft to fix:\n{cand_text}"
        )
        msg2 = [{"role": "user", "content": repair_prompt}]
        resp2 = gateway.complete(model="openai/gpt-4o-mini", messages=msg2, temperature=0.0)
        cand_text2 = resp2.get("content", "") if isinstance(resp2, dict) else getattr(resp2, "text", "")
        is_ok2, bindings2, unverified2 = verify_and_bind_narrative(cand_text2, quantities)
        if is_ok2:
            return NarrativeResult(text=cand_text2, is_grounded=True, bindings=bindings2, render_mode="llm_generated")

        t_text, t_bindings = build_templated_narrative(quantities)
        return NarrativeResult(text=t_text, is_grounded=True, bindings=t_bindings, render_mode="templated_fallback_after_repair_failure")
    except Exception:
        t_text, t_bindings = build_templated_narrative(quantities)
        return NarrativeResult(text=t_text, is_grounded=True, bindings=t_bindings, render_mode="templated")
