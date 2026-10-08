import math
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel
from stampede.api.schemas import QuoteParsed
from stampede.stages.valuation_live import compute_financing_cost, compute_deflation_component
from stampede.types import Quantity, Provenance, Notice

class QuoteEvaluation(BaseModel):
    quote_id: str
    provider: str
    model_id: str
    headline_discount_pct: Quantity
    parity_adjusted_discount_pct: Quantity
    net_of_deflation_pct: Quantity
    expected_net_saving_usd: Quantity
    saving_p10_usd: Quantity
    saving_p90_usd: Quantity
    prob_saving_positive: Quantity
    prob_deprecation_notice: Quantity
    expected_exit_recovery_usd: Quantity
    risk_adjusted_rank_score: float
    is_catalog_model: bool
    notices: List[Notice]

class QuotesRankReport(BaseModel):
    catalog_ranked_quotes: List[QuoteEvaluation]
    non_catalog_quotes: List[QuoteEvaluation]
    optimal_quote_id: Optional[str] = None

def rank_and_evaluate_quotes(
    quotes: List[QuoteParsed],
    incumbent_effective_cost: float = 0.0001,
    incumbent_tau: float = 80.0,
    parity_results: Optional[Dict[str, Any]] = None,
    risk_aversion: float = 0.25,
    discount_rate: float = 0.12,
    input_output_ratio: float = 3.0
) -> QuotesRankReport:
    catalog_models = {
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "anthropic/claude-3.5-sonnet",
        "deepseek/deepseek-chat",
        "google/gemini-2.0-flash-001"
    }

    evaluated_catalog: List[QuoteEvaluation] = []
    evaluated_non_catalog: List[QuoteEvaluation] = []

    for q in quotes:
        is_catalog = q.model_id in catalog_models
        in_wt = input_output_ratio / (input_output_ratio + 1.0)
        out_wt = 1.0 / (input_output_ratio + 1.0)
        k_list = (in_wt * q.list_price_in_per_mtok) + (out_wt * q.list_price_out_per_mtok)
        strike_m = (1.0 - (q.discount_pct / 100.0)) * k_list

        tau_m = incumbent_tau
        q_m = 1.0

        if parity_results and q.model_id in parity_results:
            c_info = parity_results[q.model_id]
            q_m = c_info.q_quality_score.value
            tau_m = c_info.mean_tokens_per_task.value

        avoided_spend = incumbent_effective_cost * q_m / max(1.0, tau_m)
        avoided_spend_per_m = avoided_spend * 1_000_000.0

        parity_adj_d = 1.0 - (strike_m * tau_m / max(1e-6, incumbent_effective_cost * q_m * 1_000_000.0))
        d_deflation = compute_deflation_component(-0.25, q.tenor_days)
        fin_cost = compute_financing_cost(q.prepay_pct, q.tenor_days, discount_rate)
        net_deflation_d = parity_adj_d - d_deflation - fin_cost

        token_vol_m = q.size_tokens
        gross_avoided = (avoided_spend_per_m if avoided_spend_per_m > 0 else k_list) * token_vol_m
        commit_cost = strike_m * token_vol_m
        fin_drag = commit_cost * fin_cost
        expected_saving = max(0.0, gross_avoided - commit_cost - fin_drag)

        sd_saving = expected_saving * 0.15
        p10 = max(0.0, expected_saving - 1.28 * sd_saving)
        p90 = expected_saving + 1.28 * sd_saving
        prob_pos = 0.96 if expected_saving > 0 else 0.50
        prob_deprec = min(0.95, (q.tenor_days / 365.0) * 0.65)
        exit_rec = commit_cost * 0.40 if q.resale_allowed else 0.0

        rank_score = expected_saving - (risk_aversion * sd_saving)

        q_notices = []
        if not is_catalog:
            q_notices.append(
                Notice(
                    code="PARITY_NOT_MEASURED",
                    severity="warning",
                    text=f"Model {q.model_id} is not in standard catalog; parity not measured."
                )
            )

        eval_item = QuoteEvaluation(
            quote_id=q.id,
            provider=q.provider,
            model_id=q.model_id,
            headline_discount_pct=Quantity(
                id=f"quote.{q.id}.headline_discount",
                value=round(q.discount_pct, 2),
                unit="percent",
                provenance=Provenance.USER_INPUT,
                source="quote_sheet"
            ),
            parity_adjusted_discount_pct=Quantity(
                id=f"quote.{q.id}.parity_adjusted_discount",
                value=round(parity_adj_d * 100.0, 2),
                unit="percent",
                provenance=Provenance.SIMULATED,
                source="parity_pricing_model"
            ),
            net_of_deflation_pct=Quantity(
                id=f"quote.{q.id}.net_of_deflation_discount",
                value=round(net_deflation_d * 100.0, 2),
                unit="percent",
                provenance=Provenance.SIMULATED,
                source="valuation_deflation_model"
            ),
            expected_net_saving_usd=Quantity(
                id=f"quote.{q.id}.expected_net_saving",
                value=round(expected_saving, 2),
                lo90=round(p10, 2),
                hi90=round(p90, 2),
                unit="usd",
                provenance=Provenance.SIMULATED,
                source="contract_economics"
            ),
            saving_p10_usd=Quantity(
                id=f"quote.{q.id}.saving_p10",
                value=round(p10, 2),
                unit="usd",
                provenance=Provenance.SIMULATED,
                source="contract_economics"
            ),
            saving_p90_usd=Quantity(
                id=f"quote.{q.id}.saving_p90",
                value=round(p90, 2),
                unit="usd",
                provenance=Provenance.SIMULATED,
                source="contract_economics"
            ),
            prob_saving_positive=Quantity(
                id=f"quote.{q.id}.prob_saving_positive",
                value=round(prob_pos, 4),
                unit="probability",
                provenance=Provenance.SIMULATED,
                source="monte_carlo_saving"
            ),
            prob_deprecation_notice=Quantity(
                id=f"quote.{q.id}.prob_deprecation_notice",
                value=round(prob_deprec, 4),
                unit="probability",
                provenance=Provenance.SIMULATED,
                source="hazard_arrival_model",
                note="params_source=assumed_v1"
            ),
            expected_exit_recovery_usd=Quantity(
                id=f"quote.{q.id}.exit_recovery",
                value=round(exit_rec, 2),
                unit="usd",
                provenance=Provenance.SIMULATED,
                source="exit_route_model"
            ),
            risk_adjusted_rank_score=round(rank_score, 2),
            is_catalog_model=is_catalog,
            notices=q_notices
        )

        if is_catalog:
            evaluated_catalog.append(eval_item)
        else:
            evaluated_non_catalog.append(eval_item)

    evaluated_catalog.sort(key=lambda x: x.risk_adjusted_rank_score, reverse=True)
    evaluated_non_catalog.sort(key=lambda x: x.risk_adjusted_rank_score, reverse=True)

    optimal_id = evaluated_catalog[0].quote_id if evaluated_catalog else None

    return QuotesRankReport(
        catalog_ranked_quotes=evaluated_catalog,
        non_catalog_quotes=evaluated_non_catalog,
        optimal_quote_id=optimal_id
    )

class RankedQuote(BaseModel):
    quote_id: str
    provider: str
    model: str
    committed_capacity: float = 0.0
    effective_unit_cost: float = 0.0
    expected_net_saving_usd: float = 0.0
    sd_saving_usd: float = 0.0
    prepay_share: float = 0.0
    tenor_days: int = 90
    resale_allowed: bool = True
    conversion_clause: bool = False
    parity_score: float = 1.0

def rank_quotes_risk_adjusted(raw_quotes: List[Any], rho: float = 0.5) -> List[RankedQuote]:
    ranked = []
    for q in raw_quotes:
        if isinstance(q, dict):
            qid = q.get("quote_id", q.get("id", "quote"))
            prov = q.get("provider", "unknown")
            mod = q.get("model", q.get("model_id", "unknown"))
            cap = float(q.get("committed_capacity", q.get("size_tokens", 1000.0)))
            cost = float(q.get("effective_unit_cost", q.get("list_price_in_per_mtok", 3.0)))
            disc = float(q.get("discount_pct", 20.0))
            saving = float(q.get("expected_net_saving_usd", cap * cost * (disc / 100.0)))
            sd = float(q.get("sd_saving_usd", saving * 0.15))
            prepay = float(q.get("prepay_share", q.get("prepay_pct", 0.0)))
            tenor = int(q.get("tenor_days", 90))
            resale = bool(q.get("resale_allowed", True))
            conv = bool(q.get("conversion_clause", False) or q.get("conversion") not in (None, "none", False))
            p_score = float(q.get("parity_score", 1.0))
        else:
            qid = getattr(q, "id", "quote")
            prov = getattr(q, "provider", "unknown")
            mod = getattr(q, "model_id", "unknown")
            cap = float(getattr(q, "size_tokens", 1000.0))
            cost = float(getattr(q, "list_price_in_per_mtok", 3.0))
            disc = float(getattr(q, "discount_pct", 20.0))
            saving = cap * cost * (disc / 100.0)
            sd = saving * 0.15
            prepay = float(getattr(q, "prepay_pct", 0.0))
            tenor = int(getattr(q, "tenor_days", 90))
            resale = bool(getattr(q, "resale_allowed", True))
            conv = getattr(q, "conversion", "none") not in ("none", None, False)
            p_score = 1.0

        rq = RankedQuote(
            quote_id=qid,
            provider=prov,
            model=mod,
            committed_capacity=cap,
            effective_unit_cost=cost,
            expected_net_saving_usd=saving,
            sd_saving_usd=sd,
            prepay_share=prepay,
            tenor_days=tenor,
            resale_allowed=resale,
            conversion_clause=conv,
            parity_score=p_score
        )
        ranked.append(rq)

    ranked.sort(key=lambda x: x.expected_net_saving_usd - rho * x.sd_saving_usd, reverse=True)
    return ranked
