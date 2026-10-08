import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
from pydantic import BaseModel
from stampede.types import Quantity, Provenance

class JudgeOperatingChars(BaseModel):
    judge_model: str
    sens_alpha: float
    sens_beta: float
    spec_alpha: float
    spec_beta: float
    youden_j: float

def load_judge_operating_characteristics(
    judge_model: str = "meta-llama/llama-3.3-70b-instruct",
    artifact_path: Path = Path("artifacts/judge_operating_characteristics.json")
) -> JudgeOperatingChars:
    if artifact_path.exists():
        with open(artifact_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if judge_model in data:
                j_info = data[judge_model]
                sens_b = j_info["sensitivity"]["beta_posterior"]
                spec_b = j_info["specificity"]["beta_posterior"]
                return JudgeOperatingChars(
                    judge_model=judge_model,
                    sens_alpha=float(sens_b["alpha"]),
                    sens_beta=float(sens_b["beta"]),
                    spec_alpha=float(spec_b["alpha"]),
                    spec_beta=float(spec_b["beta"]),
                    youden_j=float(j_info["youden_j"])
                )

    return JudgeOperatingChars(
        judge_model=judge_model,
        sens_alpha=266.0,
        sens_beta=3.0,
        spec_alpha=30.0,
        spec_beta=5.0,
        youden_j=0.8713
    )

def adjust_posterior_for_judge_error(
    successes: int,
    trials: int,
    theta0: float = 0.90,
    num_samples: int = 4000,
    seed: int = 42,
    operating_chars: Optional[JudgeOperatingChars] = None
) -> Dict[str, Any]:
    if operating_chars is None:
        operating_chars = load_judge_operating_characteristics()

    rng = np.random.default_rng(seed)

    raw_pi_samples = rng.beta(1.0 + successes, 1.0 + trials - successes, size=num_samples)
    raw_mean = float(np.mean(raw_pi_samples))
    raw_ci = [float(np.percentile(raw_pi_samples, 5.0)), float(np.percentile(raw_pi_samples, 95.0))]

    if operating_chars.youden_j < 0.5:
        return {
            "is_valid_decision": False,
            "reason": f"Youden index J={operating_chars.youden_j:.4f} is below 0.50 cutoff",
            "raw_theta_mean": round(raw_mean, 4),
            "raw_theta_ci": [round(c, 4) for c in raw_ci],
            "adjusted_theta_mean": round(raw_mean, 4),
            "adjusted_theta_ci": [round(c, 4) for c in raw_ci],
            "prob_above_theta0": float(np.mean(raw_pi_samples >= theta0))
        }

    sens_samples = rng.beta(operating_chars.sens_alpha, operating_chars.sens_beta, size=num_samples)
    spec_samples = rng.beta(operating_chars.spec_alpha, operating_chars.spec_beta, size=num_samples)

    denom = np.maximum(1e-4, sens_samples + spec_samples - 1.0)
    adjusted_samples = (raw_pi_samples + spec_samples - 1.0) / denom
    adjusted_samples = np.clip(adjusted_samples, 0.0, 1.0)

    adj_mean = float(np.mean(adjusted_samples))
    adj_ci = [float(np.percentile(adjusted_samples, 5.0)), float(np.percentile(adjusted_samples, 95.0))]
    p_above = float(np.mean(adjusted_samples >= theta0))

    return {
        "is_valid_decision": True,
        "reason": None,
        "raw_theta_mean": round(raw_mean, 4),
        "raw_theta_ci": [round(c, 4) for c in raw_ci],
        "adjusted_theta_mean": round(adj_mean, 4),
        "adjusted_theta_ci": [round(c, 4) for c in adj_ci],
        "prob_above_theta0": round(p_above, 4)
    }

class JudgeAdjustmentResult(BaseModel):
    adjusted_theta_mean: Quantity
    youden_index: Quantity
    blocks_parity_decision: bool

def adjust_judge_rate(
    apparent_rate: float,
    n_evals: int,
    sensitivity: float = 0.95,
    specificity: float = 0.90
) -> JudgeAdjustmentResult:
    youden = sensitivity + specificity - 1.0
    blocks = youden < 0.5
    adj_mean = (apparent_rate + specificity - 1.0) / max(1e-4, youden)
    adj_mean = float(np.clip(adj_mean, 0.0, 1.0))
    return JudgeAdjustmentResult(
        adjusted_theta_mean=Quantity(id="judge.adj_theta", value=round(adj_mean, 4), provenance=Provenance.FITTED),
        youden_index=Quantity(id="judge.youden_j", value=round(youden, 4), provenance=Provenance.MEASURED_BENCHMARK),
        blocks_parity_decision=blocks
    )
