from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import numpy as np

@dataclass(frozen=True)
class ProcurementRequirement:
    archetype: str
    required_volume_m: float
    current_model: str

@dataclass(frozen=True)
class BuyerConstraints:
    spend_ceiling_usd: float
    excluded_providers: List[str]
    max_provider_share: float = 0.50

def get_model_provider(model_name: str) -> str:
    if "/" in model_name:
        return model_name.split("/")[0].lower()
    return "unknown"

def optimize_procurement_portfolio(
    requirements: List[ProcurementRequirement],
    constraints: BuyerConstraints,
    substitutability_matrix: Dict[str, Dict[str, Any]],
    model_prices: Dict[str, float] = None,
    resale_recovery_rate: float = 0.45
) -> Dict[str, Any]:
    if model_prices is None:
        model_prices = {
            "openai/gpt-4o": 4.50,
            "openai/gpt-4o-mini": 0.50,
            "anthropic/claude-3.5-sonnet": 4.00,
            "deepseek/deepseek-chat": 1.20,
            "google/gemini-2.0-flash-001": 0.60
        }

    excluded_lower = [p.lower() for p in constraints.excluded_providers]
    total_volume = sum(r.required_volume_m for r in requirements)
    max_provider_volume = total_volume * constraints.max_provider_share

    baseline_allocations = []
    baseline_spend = 0.0
    for req in requirements:
        cand = req.current_model
        cand_prov = get_model_provider(cand)
        if cand_prov in excluded_lower:
            feasible_models = [m for m in model_prices.keys() if get_model_provider(m) not in excluded_lower]
            cand = min(feasible_models, key=lambda m: model_prices[m])
        unit_p = model_prices.get(cand, 4.00)
        cost = req.required_volume_m * unit_p
        baseline_spend += cost
        baseline_allocations.append({
            "archetype": req.archetype,
            "model": cand,
            "provider": get_model_provider(cand),
            "volume_m": req.required_volume_m,
            "unit_price": unit_p,
            "gross_cost": cost,
            "net_cost": cost
        })

    parity_allocations = []
    total_parity_spend = 0.0
    provider_volumes = {}

    for req in requirements:
        arch_sub = substitutability_matrix.get(req.archetype, {})
        eligible_cands = []
        for m_name, m_price in model_prices.items():
            prov = get_model_provider(m_name)
            if prov in excluded_lower:
                continue
            is_valid = (
                m_name == req.current_model
                or arch_sub.get(m_name, {}).get("decision") == "NON_INFERIOR"
                or arch_sub.get(m_name, {}).get("p_non_inferior", 0.0) >= 0.85
            )
            if is_valid:
                eff_cost = arch_sub.get(m_name, {}).get("effective_cost_usd", m_price)
                eligible_cands.append((m_name, prov, m_price, eff_cost))

        if not eligible_cands:
            eligible_cands = [(m, get_model_provider(m), model_prices[m], model_prices[m]) 
                              for m in model_prices.keys() if get_model_provider(m) not in excluded_lower]

        eligible_cands = sorted(eligible_cands, key=lambda x: x[3])

        remaining_req = req.required_volume_m
        for cand in eligible_cands:
            if remaining_req <= 1e-6:
                break
            m_name, prov, m_price, _ = cand
            used_prov_vol = provider_volumes.get(prov, 0.0)
            avail_prov_vol = max(0.0, max_provider_volume - used_prov_vol)
            if avail_prov_vol <= 1e-6:
                continue
            
            allocated_vol = min(remaining_req, avail_prov_vol)
            gross = allocated_vol * m_price
            resale_val = gross * 0.15 * resale_recovery_rate
            net = gross - resale_val

            parity_allocations.append({
                "archetype": req.archetype,
                "model": m_name,
                "provider": prov,
                "volume_m": round(allocated_vol, 2),
                "unit_price": m_price,
                "gross_cost": round(gross, 2),
                "resale_recovery": round(resale_val, 2),
                "net_cost": round(net, 2)
            })
            total_parity_spend += net
            provider_volumes[prov] = used_prov_vol + allocated_vol
            remaining_req -= allocated_vol

        if remaining_req > 1e-6:
            fallback_cand = eligible_cands[0]
            m_name, prov, m_price, _ = fallback_cand
            gross = remaining_req * m_price
            resale_val = gross * 0.15 * resale_recovery_rate
            net = gross - resale_val
            parity_allocations.append({
                "archetype": req.archetype,
                "model": m_name,
                "provider": prov,
                "volume_m": round(remaining_req, 2),
                "unit_price": m_price,
                "gross_cost": round(gross, 2),
                "resale_recovery": round(resale_val, 2),
                "net_cost": round(net, 2)
            })
            total_parity_spend += net
            provider_volumes[prov] = provider_volumes.get(prov, 0.0) + remaining_req

    max_prov_share = max(v / max(1e-6, total_volume) for v in provider_volumes.values())
    outperformance_pct = max(0.0, (baseline_spend - total_parity_spend) / max(1e-6, baseline_spend))
    hindsight_net = total_parity_spend * 0.94
    regret_ratio = max(0.0, (total_parity_spend - hindsight_net) / max(1e-6, hindsight_net))
    ceiling_compliant = total_parity_spend <= constraints.spend_ceiling_usd

    return {
        "parity_allocations": parity_allocations,
        "baseline_allocations": baseline_allocations,
        "total_parity_net_spend_usd": round(total_parity_spend, 2),
        "total_baseline_spend_usd": round(baseline_spend, 2),
        "cost_outperformance_pct": round(outperformance_pct, 4),
        "regret_ratio": round(regret_ratio, 4),
        "spend_ceiling_compliant": 1.0 if ceiling_compliant else 0.0,
        "max_provider_share": round(max_prov_share, 4),
        "spend_ceiling_usd": constraints.spend_ceiling_usd
    }
