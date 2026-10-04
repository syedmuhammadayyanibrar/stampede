import math
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from scipy.optimize import minimize

class HazardModelResult:
    def __init__(
        self,
        model_type: str,
        parameters: Dict[str, float],
        log_likelihood: float,
        event_count: int,
        total_exposure_years: float
    ) -> None:
        self.model_type = model_type
        self.parameters = parameters
        self.log_likelihood = log_likelihood
        self.event_count = event_count
        self.total_exposure_years = total_exposure_years

    def survival_probability(self, time_years: float) -> float:
        if self.model_type == "exponential":
            lam = self.parameters.get("rate", 0.5)
            return float(math.exp(-lam * max(0.0, time_years)))
        elif self.model_type == "weibull":
            scale = max(1e-4, self.parameters.get("scale", 1.0))
            shape = max(1e-4, self.parameters.get("shape", 1.0))
            return float(math.exp(-((max(0.0, time_years) / scale) ** shape)))
        return float(math.exp(-0.5 * max(0.0, time_years)))

    def cumulative_event_probability(self, time_years: float) -> float:
        return float(1.0 - self.survival_probability(time_years))

def fit_exponential_hazard(
    durations_years: List[float],
    event_observed: List[int]
) -> HazardModelResult:
    durs = np.array(durations_years, dtype=np.float64)
    obs = np.array(event_observed, dtype=np.int32)
    events = int(np.sum(obs))
    total_exposure = float(np.sum(durs))

    if total_exposure <= 0.0 or events == 0:
        rate = 0.50
        ll = -100.0
    else:
        rate = events / total_exposure
        ll = float(events * math.log(max(1e-8, rate)) - (rate * total_exposure))

    return HazardModelResult(
        model_type="exponential",
        parameters={"rate": float(rate)},
        log_likelihood=ll,
        event_count=events,
        total_exposure_years=total_exposure
    )

def fit_weibull_hazard(
    durations_years: List[float],
    event_observed: List[int]
) -> HazardModelResult:
    durs = np.array(durations_years, dtype=np.float64)
    obs = np.array(event_observed, dtype=np.int32)
    events = int(np.sum(obs))
    total_exposure = float(np.sum(durs))

    if events == 0 or total_exposure <= 0.0:
        return HazardModelResult(
            model_type="weibull",
            parameters={"scale": 1.0, "shape": 1.0},
            log_likelihood=-100.0,
            event_count=0,
            total_exposure_years=total_exposure
        )

    def neg_log_likelihood(params: np.ndarray) -> float:
        scale, shape = params
        if scale <= 1e-4 or shape <= 1e-4:
            return 1e9
        log_h = np.log(shape) - np.log(scale) + (shape - 1.0) * (np.log(np.maximum(1e-6, durs)) - np.log(scale))
        cum_h = (durs / scale) ** shape
        ll = np.sum(obs * log_h - cum_h)
        return float(-ll)

    init_guess = np.array([max(0.5, total_exposure / max(1, events)), 1.1])
    res = minimize(neg_log_likelihood, init_guess, bounds=[(0.05, 20.0), (0.1, 5.0)])
    
    scale_opt, shape_opt = res.x
    ll_opt = float(-res.fun)

    return HazardModelResult(
        model_type="weibull",
        parameters={"scale": float(scale_opt), "shape": float(shape_opt)},
        log_likelihood=ll_opt,
        event_count=events,
        total_exposure_years=total_exposure
    )

def cluster_bootstrap_hazard(
    provider_clusters: Dict[str, List[Tuple[float, int]]],
    num_bootstrap: int = 1000,
    seed: int = 42,
    min_clusters: int = 6
) -> Dict[str, Any]:
    providers = list(provider_clusters.keys())
    if len(providers) < min_clusters:
        return {
            "status": "INCONCLUSIVE",
            "reason": f"Cluster count {len(providers)} is below required minimum {min_clusters}",
            "bootstrap_rates": []
        }

    rng = np.random.default_rng(seed)
    boot_rates = []

    for _ in range(num_bootstrap):
        sampled_providers = rng.choice(providers, size=len(providers), replace=True)
        sampled_durs = []
        sampled_obs = []
        for prov in sampled_providers:
            for dur, ev in provider_clusters[prov]:
                sampled_durs.append(dur)
                sampled_obs.append(ev)

        fit = fit_exponential_hazard(sampled_durs, sampled_obs)
        boot_rates.append(fit.parameters["rate"])

    rates_arr = np.array(boot_rates)
    return {
        "status": "PASS",
        "mean_rate": float(np.mean(rates_arr)),
        "ci_95": [float(np.percentile(rates_arr, 2.5)), float(np.percentile(rates_arr, 97.5))],
        "bootstrap_rates": [float(r) for r in boot_rates[:20]]
    }
