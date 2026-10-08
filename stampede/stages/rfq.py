from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from stampede.types import Quantity, Provenance
from stampede.stages.planner import PlanResult
from parity.agent.grounding import verify_narrative_grounding

class AcceptableModelSpec(BaseModel):
    model: str
    min_parity_threshold: float
    measured_parity_score: float

class StructuredRFQ(BaseModel):
    rfq_id: str
    workload_mix: Dict[str, float]
    measured_tokens_per_task: Dict[str, int]
    acceptable_models: List[AcceptableModelSpec]
    tenor_days: int
    quantity_min: float
    quantity_max: float
    max_strike_per_token_usd: float
    resale_clause_required: bool
    conversion_clause_required: bool
    delivery_profile: Dict[str, float]
    evaluation_criteria: List[str]
    email_text: str = ""
    email_render_mode: str = "deterministic_template"

def build_structured_rfq(
    plan: PlanResult,
    workload_mix: Dict[str, float],
    tokens_per_task: Dict[str, int],
    reservation_strike: float,
    tenor_days: int = 90,
    resale_required: bool = False,
    conversion_required: bool = False
) -> StructuredRFQ:
    q_val = plan.optimal_sizing_q_star.value
    acceptable = []
    for alloc in plan.allocations:
        if alloc.model != "incumbent":
            acceptable.append(AcceptableModelSpec(
                model=alloc.model,
                min_parity_threshold=0.90,
                measured_parity_score=0.95
            ))
    if not acceptable:
        acceptable.append(AcceptableModelSpec(
            model="incumbent",
            min_parity_threshold=1.00,
            measured_parity_score=1.00
        ))

    criteria = [
        "SLA availability >= 99.9%",
        "Target throughput provisioned at peak hours",
        "Deterministic latency p95 <= 1500ms"
    ]
    if resale_required:
        criteria.append("Secondary transfer / resale allowed")
    if conversion_required:
        criteria.append("Model conversion to successor version at par")

    rfq = StructuredRFQ(
        rfq_id="rfq_stampede_01",
        workload_mix=workload_mix,
        measured_tokens_per_task=tokens_per_task,
        acceptable_models=acceptable,
        tenor_days=tenor_days,
        quantity_min=round(q_val * 0.8, 2),
        quantity_max=round(q_val * 1.2, 2),
        max_strike_per_token_usd=reservation_strike,
        resale_clause_required=resale_required,
        conversion_clause_required=conversion_required,
        delivery_profile={"q1": round(q_val * 0.25, 2), "q2": round(q_val * 0.25, 2), "q3": round(q_val * 0.25, 2), "q4": round(q_val * 0.25, 2)},
        evaluation_criteria=criteria
    )

    rfq.email_text = render_rfq_email_template(rfq)
    rfq.email_render_mode = "deterministic_template"
    return rfq

def render_rfq_email_template(rfq: StructuredRFQ) -> str:
    models_str = ", ".join([m.model for m in rfq.acceptable_models])
    return (
        f"Subject: Request for Quote - Inference Capacity ({rfq.tenor_days} Days)\n\n"
        f"Dear Partner,\n\n"
        f"We are soliciting firm quotes for dedicated inference capacity over a {rfq.tenor_days}-day period. "
        f"Our target volume ranges from {rfq.quantity_min:.2f} to {rfq.quantity_max:.2f} units, "
        f"with maximum acceptable strike price of ${rfq.max_strike_per_token_usd:.6f} per token.\n\n"
        f"Acceptable model specifications: {models_str}.\n"
        f"Resale clause required: {'Yes' if rfq.resale_clause_required else 'No'}.\n"
        f"Conversion clause required: {'Yes' if rfq.conversion_clause_required else 'No'}.\n\n"
        f"Please provide your term sheet within 5 business days.\n\n"
        f"Regards,\nProcurement Team [templated narrative]"
    )

def render_rfq_email_with_llm(rfq: StructuredRFQ, gateway: Any) -> str:
    has_key = bool(getattr(gateway, "api_key", None)) or bool(getattr(gateway, "has_key", False))
    if not gateway or not has_key:
        return render_rfq_email_template(rfq)

    prompt = (
        f"Write a formal RFQ procurement email using ONLY the following facts:\n"
        f"Tenor: {rfq.tenor_days} days\n"
        f"Quantity range: {rfq.quantity_min} to {rfq.quantity_max}\n"
        f"Max strike price: ${rfq.max_strike_per_token_usd:.6f}\n"
        f"Models: {', '.join([m.model for m in rfq.acceptable_models])}\n"
        f"Do not introduce any other numbers or prices."
    )
    try:
        msg = [{"role": "user", "content": prompt}]
        resp = gateway.complete(model="openai/gpt-4o-mini", messages=msg, temperature=0.0)
        cand_text = resp.get("content", "") if isinstance(resp, dict) else getattr(resp, "text", "")
        gt_data = rfq.model_dump()
        check = verify_narrative_grounding(cand_text, gt_data)
        if check["is_grounded"]:
            return cand_text

        repair_prompt = (
            f"The previous draft contained ungrounded numbers: {check['unverified_numbers']}. "
            f"Rewrite the RFQ email removing or correcting those numbers to match exactly:\n"
            f"Tenor: {rfq.tenor_days}, Quantity min: {rfq.quantity_min}, max: {rfq.quantity_max}, strike: {rfq.max_strike_per_token_usd:.6f}.\n"
            f"Draft:\n{cand_text}"
        )
        msg2 = [{"role": "user", "content": repair_prompt}]
        resp2 = gateway.complete(model="openai/gpt-4o-mini", messages=msg2, temperature=0.0)
        cand_text2 = resp2.get("content", "") if isinstance(resp2, dict) else getattr(resp2, "text", "")
        check2 = verify_narrative_grounding(cand_text2, gt_data)
        if check2["is_grounded"]:
            return cand_text2
        return render_rfq_email_template(rfq)
    except Exception:
        return render_rfq_email_template(rfq)
