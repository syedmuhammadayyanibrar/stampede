import os
from typing import Dict, Any

def generate_market_narrative(experiment_data: Dict[str, Any]) -> Dict[str, str]:
    lcr_bm = experiment_data["lcr_benchmark"]
    lcr_bm_low = experiment_data["lcr_benchmark_ci_lower"]
    lcr_bm_high = experiment_data["lcr_benchmark_ci_upper"]
    lcr_sp = experiment_data["lcr_spread"]
    lcr_sp_low = experiment_data["lcr_spread_ci_lower"]
    lcr_sp_high = experiment_data["lcr_spread_ci_upper"]
    spread_norm = experiment_data["resale_spread_normal"]
    spread_shock = experiment_data["resale_spread_shock"]
    f0 = experiment_data["fair_forward_price"]
    cost_spot_sh = experiment_data["fair_cost_spot_shock"]
    cost_fwd_sh = experiment_data["fair_cost_fwd_actual_shock"]
    shock_penalty = experiment_data["fair_total_shock_penalty"]
    shock_penalty_pct = experiment_data["fair_total_shock_penalty_pct"]
    liq_blowout = experiment_data["fair_liquidity_blowout_penalty"]
    naive_penalty = experiment_data["naive_net_cost_penalty"]
    naive_penalty_pct = experiment_data["naive_net_cost_penalty_pct"]
    
    fallback_headline = (
        f"Touchmark's secondary resale mechanism exhibits a primary Benchmark Liquidity Crunch Ratio of {lcr_bm:.2f}x "
        f"(95% CI: [{lcr_bm_low:.2f}x, {lcr_bm_high:.2f}x]) relative to unshocked counterfactual value, with secondary market "
        f"spreads widening by {lcr_sp:.2f}x (95% CI: [{lcr_sp_low:.2f}x, {lcr_sp_high:.2f}x]) from {spread_norm:.1%} to {spread_shock:.1%}."
    )
    fallback_economic = (
        f"Isolating deflation from liquidity risk: entering at the engine's fair-value forward price (${f0:.2f}/M) yields expected "
        f"parity unconditionally, but conditional on a correlated shock window, the forward holder pays an expected net cost of "
        f"${cost_fwd_sh:.3f}/M versus ${cost_spot_sh:.3f}/M on spot (+{shock_penalty_pct:.1f}% penalty, +${shock_penalty:.3f}/M). "
        f"Secondary market spread blowout alone accounts for +${liq_blowout:.3f}/M in unrecovered liquidation friction, while entering "
        f"at a naive 15% spot discount adds another +{naive_penalty_pct:.1f}% (+${naive_penalty:.3f}/M) penalty from unhedged hardware deflation."
    )
    
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key and os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("GOOGLE_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
    
    if not api_key:
        return {
            "source": "deterministic_prewritten",
            "headline_summary": fallback_headline,
            "economic_summary": fallback_economic
        }
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = f"""
You are a quantitative risk engineer reviewing a simulation of Touchmark's AI inference forward contracts.
Synthesize the following deterministic outputs into an institutional risk assessment for quantitative founders.
Do NOT alter any numbers or invent new statistics. Every number in your text must match the inputs below.

NUMERICAL INPUTS:
- Fair Forward Price F0: ${f0:.2f} / M tokens
- Primary Benchmark Liquidity Crunch Ratio (vs unshocked benchmark): {lcr_bm:.2f}x (95% CI: [{lcr_bm_low:.2f}x, {lcr_bm_high:.2f}x])
- Robustness Microstructural Spread Ratio: {lcr_sp:.2f}x (95% CI: [{lcr_sp_low:.2f}x, {lcr_sp_high:.2f}x])
- Normal spread: {spread_norm:.1%} | Shock spread: {spread_shock:.1%}
- Fair Forward Net Cost in Shock Window: ${cost_fwd_sh:.3f} / M tokens
- Spot On-Demand Cost in Shock Window: ${cost_spot_sh:.3f} / M tokens
- Total Shock Net Cost Penalty: +${shock_penalty:.3f} / M tokens (+{shock_penalty_pct:.1f}%)
- Cost from Secondary Spread Blowout Alone: +${liq_blowout:.3f} / M tokens
- Naive 15% Discount Lock-in Penalty (deflation alone): +${naive_penalty:.3f} / M tokens (+{naive_penalty_pct:.1f}%)

REQUIREMENTS:
1. Deliver exactly two short paragraphs.
2. Paragraph 1: Headline finding defining both LCR metrics (primary benchmark vs unshocked counterfactual, and robustness spread ratio).
3. Paragraph 2: Economic risk decomposition distinguishing (a) the naive 15% discount deflation drag from (b) the fair-value shock penalty and the secondary market spread blowout.
4. Tone: Rigorous, quantitative, institutional, zero marketing fluff.
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = response.text.strip()
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        if len(parts) >= 2:
            return {
                "source": "gemini-2.5-flash",
                "headline_summary": parts[0],
                "economic_summary": parts[1]
            }
        else:
            return {
                "source": "gemini-2.5-flash",
                "headline_summary": text,
                "economic_summary": fallback_economic
            }
    except Exception:
        return {
            "source": "deterministic_fallback_on_exception",
            "headline_summary": fallback_headline,
            "economic_summary": fallback_economic
        }
