import math
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from scipy import stats

def compute_wilson_ci(
    successes: int,
    total: int,
    confidence: float = 0.95
) -> Tuple[float, float]:
    if total <= 0:
        return (0.0, 1.0)
    p_hat = successes / total
    z = stats.norm.ppf(1.0 - (1.0 - confidence) / 2.0)
    denom = 1.0 + (z**2 / total)
    center = (p_hat + (z**2 / (2.0 * total))) / denom
    spread = z * math.sqrt((p_hat * (1.0 - p_hat) / total) + (z**2 / (4.0 * total**2))) / denom
    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)
    return (float(lower), float(upper))

def compute_difference_wilson_ci(
    successes_1: int,
    total_1: int,
    successes_2: int,
    total_2: int,
    confidence: float = 0.80
) -> Tuple[float, float]:
    p1 = successes_1 / max(1, total_1)
    p2 = successes_2 / max(1, total_2)
    l1, u1 = compute_wilson_ci(successes_1, total_1, confidence=confidence)
    l2, u2 = compute_wilson_ci(successes_2, total_2, confidence=confidence)
    diff = p1 - p2
    delta_low = diff - math.sqrt((p1 - l1)**2 + (u2 - p2)**2)
    delta_high = diff + math.sqrt((u1 - p1)**2 + (p2 - l2)**2)
    return (float(delta_low), float(delta_high))

def compute_posterior_beta(
    prior_alpha: float,
    prior_beta: float,
    successes: int,
    trials: int
) -> Tuple[float, float]:
    return (prior_alpha + successes, prior_beta + (trials - successes))

def probability_non_inferior(
    alpha_cand: float,
    beta_cand: float,
    alpha_inc: float,
    beta_inc: float,
    delta: float = 0.05,
    num_samples: int = 10000,
    seed: int = 42
) -> float:
    rng = np.random.default_rng(seed)
    samples_cand = rng.beta(alpha_cand, beta_cand, size=num_samples)
    samples_inc = rng.beta(alpha_inc, beta_inc, size=num_samples)
    non_inf_count = np.sum(samples_cand >= (samples_inc - delta))
    return float(non_inf_count / num_samples)

def check_sequential_stopping(
    p_non_inf: float,
    current_n: int,
    min_n: int = 15,
    max_n: int = 60,
    threshold_pass: float = 0.95,
    threshold_fail: float = 0.05
) -> Tuple[bool, str]:
    if current_n < min_n:
        return (False, "CONTINUE")
    if p_non_inf >= threshold_pass:
        return (True, "NON_INFERIOR")
    if p_non_inf <= threshold_fail:
        return (True, "INFERIOR")
    if current_n >= max_n:
        return (True, "INCONCLUSIVE")
    return (False, "CONTINUE")

def compute_effective_cost(
    raw_task_cost_usd: float,
    theta_mean: float
) -> float:
    safe_theta = max(1e-4, theta_mean)
    return float(raw_task_cost_usd / safe_theta)

def compute_spearman_rho(
    ranks_x: List[float],
    ranks_y: List[float]
) -> float:
    if len(ranks_x) < 2 or len(ranks_x) != len(ranks_y):
        return 0.0
    res = stats.spearmanr(ranks_x, ranks_y)
    statistic = getattr(res, "statistic", getattr(res, "correlation", 0.0))
    if math.isnan(statistic):
        return 0.0
    return float(statistic)

def compute_brier_score(
    predicted_probabilities: List[float],
    true_labels: List[int]
) -> float:
    if not predicted_probabilities or len(predicted_probabilities) != len(true_labels):
        return 0.0
    p = np.array(predicted_probabilities)
    y = np.array(true_labels)
    return float(np.mean((p - y) ** 2))
