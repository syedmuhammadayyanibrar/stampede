import os
import re
from typing import Dict, Any, List
from .sizing import ContractRecommendation
from .parser import UsageSummary
from .forecast import ForecastResult

def ground_numbers_check(text: str, allowed_values: List[float], rel_tol: float = 0.02) -> bool:
    clean_text = re.sub(r",(?=\d{3})", "", text)
    numbers_in_text = re.findall(r"\b\d+(?:\.\d+)?\b", clean_text)
    if not numbers_in_text:
        return True
        
    for s_num in numbers_in_text:
        val = float(s_num)
        if val in (0, 1, 2, 3, 4, 5, 10, 14, 20, 30, 60, 90, 100, 365):
            continue
        matched = False
        for allowed in allowed_values:
            if abs(val - allowed) <= max(1.0, rel_tol * max(1.0, abs(allowed))):
                matched = True
                break
        if not matched:
            return False
    return True

def generate_copilot_explanation(
    rec: ContractRecommendation,
    summary: UsageSummary,
    forecast: ForecastResult
) -> Dict[str, str]:
    fallback_text = (
        f"Based on {summary.num_days} days of historical API token demand averaging {summary.mean_daily_tokens_millions:.2f}M tokens/day, "
        f"Touchmark's newsvendor optimization recommends a {forecast.horizon_days}-day forward commitment of {rec.optimal_notional_m:.1f}M tokens "
        f"at ${rec.forward_strike_per_m:.2f}/M. This contract is projected to yield ${rec.expected_savings:,.0f} in expected procurement savings "
        f"({rec.savings_pct:.1f}% discount vs floating spot), while sizing against an empirical {rec.crunch_exposure_penalty:.0f} dollar liquidation drag. "
        f"We recommend structuring this via the {rec.portfolio_mix['strategy_name']} ({rec.portfolio_mix['specific_model_notional_m']}M specific / "
        f"{rec.portfolio_mix['best_in_class_notional_m']}M best-in-class) across {rec.portfolio_mix['delivery_structure']}."
    )
    
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {
            "source": "deterministic_template",
            "explanation": fallback_text
        }
        
    allowed_numbers = [
        float(summary.num_days),
        float(summary.mean_daily_tokens_millions),
        float(forecast.horizon_days),
        float(rec.optimal_notional_m),
        float(rec.forward_strike_per_m),
        float(rec.expected_savings),
        float(rec.savings_pct),
        float(rec.crunch_exposure_penalty),
        float(rec.portfolio_mix["specific_model_notional_m"]),
        float(rec.portfolio_mix["best_in_class_notional_m"])
    ]
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = f"""
Summarize this Touchmark forward token contract recommendation in 2 concise sentences for a quant buyer.
Every number you mention MUST strictly come from these exact figures:
- Historical days: {summary.num_days}
- Mean daily tokens: {summary.mean_daily_tokens_millions:.2f}M
- Recommended notional: {rec.optimal_notional_m:.1f}M tokens
- Strike price: ${rec.forward_strike_per_m:.2f}/M
- Expected savings: ${rec.expected_savings:,.0f} ({rec.savings_pct:.1f}%)
- Specific model share: {rec.portfolio_mix['specific_model_notional_m']}M
- Best in class share: {rec.portfolio_mix['best_in_class_notional_m']}M
"""
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        cand_text = resp.text.strip()
        if ground_numbers_check(cand_text, allowed_numbers):
            return {
                "source": "gemini-2.5-flash",
                "explanation": cand_text
            }
        return {
            "source": "grounding_fallback",
            "explanation": fallback_text
        }
    except Exception:
        return {
            "source": "exception_fallback",
            "explanation": fallback_text
        }
