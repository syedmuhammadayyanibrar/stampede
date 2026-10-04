from dataclasses import dataclass
from typing import Dict, Tuple, Optional
import numpy as np

@dataclass(frozen=True)
class ModelCalibration:
    provider: str
    family_name: str
    spot_price_initial: float
    annual_drift: float
    annual_volatility: float
    hazard_rate_annual: float
    jump_mean: float
    base_spread: float
    shock_spread: float

@dataclass(frozen=True)
class ForwardContractSpec:
    contract_id: str
    model_family: str
    notional_tokens_millions: float
    strike_price: float
    tenor_days: int
    resale_window_days: int

@dataclass
class MarketScenario:
    switch_share: float = 0.60
    switch_share_samples: Optional[np.ndarray] = None
    absorbing_depth: float = 0.0
    conversion_rate: float = 0.0
    hazard_multiplier: Tuple[float, ...] = ()
    utilization_samples: Optional[np.ndarray] = None
    contract_type: str = "specific"

@dataclass(frozen=True)
class LiquidityCalibration:
    base_spread: float = 0.06
    shock_spread_target: float = 0.38
    impact_exponent: float = 0.5
    daily_volume_ratio: float = 0.02
    impact_constant: float = 0.75

CALIBRATED_MODELS: Dict[str, ModelCalibration] = {
    "openai_gpt_tier": ModelCalibration(
        provider="OpenAI",
        family_name="GPT-4 / 4o Frontier Tier",
        spot_price_initial=5.00,
        annual_drift=-0.35,
        annual_volatility=0.28,
        hazard_rate_annual=1.85,
        jump_mean=0.45,
        base_spread=0.06,
        shock_spread=0.38
    ),
    "anthropic_claude_tier": ModelCalibration(
        provider="Anthropic",
        family_name="Claude 3 / 3.5 Sonnet Tier",
        spot_price_initial=3.00,
        annual_drift=-0.18,
        annual_volatility=0.22,
        hazard_rate_annual=0.60,
        jump_mean=0.40,
        base_spread=0.05,
        shock_spread=0.32
    )
}
