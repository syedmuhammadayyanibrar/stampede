from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field
from scipy.optimize import milp, LinearConstraint, Bounds
from stampede.types import Quantity, Provenance
from stampede.stages.constraints_parse import ParsedConstraints

class PortfolioAllocation(BaseModel):
    option_id: str
    option_type: str
    model: str
    provider: str
    share_pct: float
    capacity: float
    expected_spend_usd: float
    expected_saving_usd: float
    sd_saving_usd: float

class RejectedOption(BaseModel):
    option_id: str
    reason: str
    binding_constraint: str

class PlanResult(BaseModel):
    allocations: List[PortfolioAllocation]
    rejected_options: List[RejectedOption]
    total_spend_usd: Quantity
    total_saving_usd: Quantity
    risk_adjusted_saving_usd: Quantity
    optimal_sizing_q_star: Quantity
    baseline_spend_usd: Quantity
    constraints_applied: Dict[str, Any]

def solve_plan(
    quotes_ranked: List[Dict[str, Any]],
    q_star: float,
    baseline_spend: float,
    constraints: Optional[ParsedConstraints] = None,
    rho: float = 0.5,
    parity_candidates: Optional[Dict[str, Dict[str, Any]]] = None
) -> PlanResult:
    c_dict = constraints.to_dict() if constraints else {}
    excluded_providers = [p.lower() for p in c_dict.get("excluded_providers", [])]
    allowed_models = [m.lower() for m in c_dict.get("allowed_models", [])]
    max_spend = c_dict.get("max_spend_usd", float("inf"))
    min_parity = c_dict.get("min_parity", 0.0)
    min_tenor = c_dict.get("min_tenor_days", 0)
    max_tenor = c_dict.get("max_tenor_days", 3650)
    max_prepay = c_dict.get("max_prepay_pct", 1.0)
    req_resale = c_dict.get("require_resale", False)
    req_conv = c_dict.get("require_conversion", False)
    max_prov_share = c_dict.get("max_provider_share", 1.0)

    rejected: List[RejectedOption] = []
    eligible_options: List[Dict[str, Any]] = []

    eligible_options.append({
        "id": "stay_on_demand",
        "type": "on_demand",
        "model": "incumbent",
        "provider": "incumbent",
        "capacity": q_star,
        "spend": baseline_spend,
        "saving": 0.0,
        "sd": 0.0,
        "prepay_pct": 0.0,
        "tenor_days": 0
    })

    if parity_candidates:
        for cand_name, cand_info in parity_candidates.items():
            cand_model = cand_info.get("model", cand_name)
            cand_prov = cand_info.get("provider", "unknown")
            is_parity = cand_info.get("decision") == "parity"
            p_score = cand_info.get("parity_score", 1.0)
            if not is_parity or p_score < min_parity:
                rejected.append(RejectedOption(
                    option_id=f"switch_on_demand_{cand_model}",
                    reason=f"Model does not meet minimum parity {min_parity}",
                    binding_constraint="min_parity"
                ))
                continue
            if cand_prov.lower() in excluded_providers:
                rejected.append(RejectedOption(
                    option_id=f"switch_on_demand_{cand_model}",
                    reason=f"Provider {cand_prov} is excluded",
                    binding_constraint="excluded_providers"
                ))
                continue
            if allowed_models and cand_model.lower() not in allowed_models:
                rejected.append(RejectedOption(
                    option_id=f"switch_on_demand_{cand_model}",
                    reason=f"Model {cand_model} not in allowed models",
                    binding_constraint="allowed_models"
                ))
                continue

            cand_cost = cand_info.get("on_demand_spend", baseline_spend * 0.7)
            cand_saving = max(0.0, baseline_spend - cand_cost)
            eligible_options.append({
                "id": f"switch_on_demand_{cand_model}",
                "type": "switch_on_demand",
                "model": cand_model,
                "provider": cand_prov,
                "capacity": q_star,
                "spend": cand_cost,
                "saving": cand_saving,
                "sd": cand_info.get("sd_saving", cand_saving * 0.1),
                "prepay_pct": 0.0,
                "tenor_days": 0
            })

    for q in quotes_ranked:
        qid = q.get("quote_id", "quote")
        prov = q.get("provider", "unknown")
        mod = q.get("model", "unknown")
        tenor = q.get("tenor_days", 90)
        prepay = q.get("prepay_share", 0.0)
        has_resale = q.get("resale_allowed", False)
        has_conv = q.get("conversion_clause", False)
        q_parity = q.get("parity_score", 1.0)

        if prov.lower() in excluded_providers:
            rejected.append(RejectedOption(option_id=qid, reason=f"Provider {prov} is excluded", binding_constraint="excluded_providers"))
            continue
        if allowed_models and mod.lower() not in allowed_models:
            rejected.append(RejectedOption(option_id=qid, reason=f"Model {mod} not in allowed models", binding_constraint="allowed_models"))
            continue
        if q_parity < min_parity:
            rejected.append(RejectedOption(option_id=qid, reason=f"Parity {q_parity:.2f} below {min_parity}", binding_constraint="min_parity"))
            continue
        if tenor < min_tenor:
            rejected.append(RejectedOption(option_id=qid, reason=f"Tenor {tenor}d below min {min_tenor}d", binding_constraint="min_tenor_days"))
            continue
        if tenor > max_tenor:
            rejected.append(RejectedOption(option_id=qid, reason=f"Tenor {tenor}d above max {max_tenor}d", binding_constraint="max_tenor_days"))
            continue
        if prepay > max_prepay:
            rejected.append(RejectedOption(option_id=qid, reason=f"Prepay {prepay:.1%} exceeds max {max_prepay:.1%}", binding_constraint="max_prepay_pct"))
            continue
        if req_resale and not has_resale:
            rejected.append(RejectedOption(option_id=qid, reason="Resale clause required", binding_constraint="require_resale"))
            continue
        if req_conv and not has_conv:
            rejected.append(RejectedOption(option_id=qid, reason="Conversion clause required", binding_constraint="require_conversion"))
            continue

        q_size = q.get("committed_capacity", q_star)
        unit_price = q.get("effective_unit_cost", 1.0)
        saving_full = q.get("expected_net_saving_usd", 0.0)
        sd_full = q.get("sd_saving_usd", saving_full * 0.15)

        for frac in [0.25, 0.50, 0.75, 1.0]:
            eff_cap = min(q_size * frac, q_star)
            frac_scale = eff_cap / max(q_size, 1e-6)
            opt_id = f"{qid}_size_{int(frac*100)}"
            opt_spend = unit_price * eff_cap
            opt_saving = saving_full * frac_scale
            opt_sd = sd_full * frac_scale

            if opt_spend > max_spend:
                rejected.append(RejectedOption(option_id=opt_id, reason=f"Spend ${opt_spend:.0f} exceeds max ${max_spend:.0f}", binding_constraint="max_spend_usd"))
                continue

            eligible_options.append({
                "id": opt_id,
                "type": "committed_quote",
                "model": mod,
                "provider": prov,
                "capacity": eff_cap,
                "spend": opt_spend,
                "saving": opt_saving,
                "sd": opt_sd,
                "prepay_pct": prepay,
                "tenor_days": tenor
            })

    best_opt = eligible_options[0]
    best_obj = -float("inf")

    for opt in eligible_options:
        obj = opt["saving"] - rho * opt["sd"]
        if obj > best_obj:
            best_obj = obj
            best_opt = opt

    allocations = [
        PortfolioAllocation(
            option_id=best_opt["id"],
            option_type=best_opt["type"],
            model=best_opt["model"],
            provider=best_opt["provider"],
            share_pct=100.0,
            capacity=best_opt["capacity"],
            expected_spend_usd=best_opt["spend"],
            expected_saving_usd=best_opt["saving"],
            sd_saving_usd=best_opt["sd"]
        )
    ]

    tot_spend = best_opt["spend"]
    tot_saving = best_opt["saving"]
    risk_adj = tot_saving - rho * best_opt["sd"]

    return PlanResult(
        allocations=allocations,
        rejected_options=rejected,
        total_spend_usd=Quantity(value=tot_spend, provenance=Provenance.FITTED),
        total_saving_usd=Quantity(value=tot_saving, provenance=Provenance.FITTED),
        risk_adjusted_saving_usd=Quantity(value=risk_adj, provenance=Provenance.FITTED),
        optimal_sizing_q_star=Quantity(value=q_star, provenance=Provenance.FITTED),
        baseline_spend_usd=Quantity(value=baseline_spend, provenance=Provenance.MEASURED_LIVE),
        constraints_applied=c_dict
    )
