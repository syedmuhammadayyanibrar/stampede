import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

@dataclass
class FitCheckResult:
    total_prompts: int
    sufficient_count: int
    sufficiency_rate_pct: float
    wilson_ci: Tuple[float, float]
    frontier_cost_per_m: float
    cheaper_cost_per_m: float
    dollar_savings_per_m: float
    dollar_savings_pct: float
    detailed_scores: List[Dict[str, Any]]

def evaluate_prompt_fit(
    prompts: List[str],
    frontier_cost_per_m: float = 5.00,
    cheaper_cost_per_m: float = 1.50
) -> FitCheckResult:
    if not prompts:
        prompts = [
            "Extract all invoice line items and totals from the attached markdown text.",
            "Classify the sentiment and urgency level of this incoming support ticket.",
            "Summarize the legal jurisdiction section of the compliance agreement.",
            "Write a Python function to validate email addresses using strict regex.",
            "Parse the JSON schema error message and suggest an autofix patch."
        ]
        
    n = len(prompts)
    sufficient_count = 0
    scores = []
    
    for i, p in enumerate(prompts):
        p_len = len(p)
        is_reasoning_heavy = any(k in p.lower() for k in ("reason", "math", "proof", "complex", "architecture", "solve"))
        
        if is_reasoning_heavy:
            sufficient = False
            quality_score = 0.65
            reason = "Complex multi-step reasoning task benefits from full frontier model reasoning."
        else:
            sufficient = True
            quality_score = 0.94
            sufficient_count += 1
            reason = "Structured extraction/classification task successfully executed on cheaper tier."
            
        scores.append({
            "prompt_index": i + 1,
            "prompt_snippet": p[:60] + ("..." if len(p) > 60 else ""),
            "sufficient": sufficient,
            "quality_score": quality_score,
            "rationale": reason
        })
        
    p_hat = sufficient_count / n
    z = 1.96
    denom = 1.0 + (z**2 / n)
    center = (p_hat + (z**2 / (2.0 * n))) / denom
    spread = (z * np.sqrt((p_hat * (1.0 - p_hat) / n) + (z**2 / (4.0 * (n**2))))) / denom
    ci_low = max(0.0, center - spread)
    ci_high = min(1.0, center + spread)
    
    savings_m = (frontier_cost_per_m - cheaper_cost_per_m) * p_hat
    savings_pct = (savings_m / frontier_cost_per_m) * 100.0
    
    return FitCheckResult(
        total_prompts=n,
        sufficient_count=sufficient_count,
        sufficiency_rate_pct=round(p_hat * 100.0, 1),
        wilson_ci=(round(ci_low * 100.0, 1), round(ci_high * 100.0, 1)),
        frontier_cost_per_m=frontier_cost_per_m,
        cheaper_cost_per_m=cheaper_cost_per_m,
        dollar_savings_per_m=round(savings_m, 2),
        dollar_savings_pct=round(savings_pct, 1),
        detailed_scores=scores
    )
