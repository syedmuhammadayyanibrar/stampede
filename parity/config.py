from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
from pydantic import BaseModel, Field

class SubstitutabilityConfig(BaseModel):
    archetypes: List[str] = Field(default_factory=lambda: [
        "code_generation",
        "structured_extraction",
        "summarization",
        "creative_writing",
        "reasoning_math",
        "rag_qa",
        "classification",
        "translation"
    ])
    prior_alpha: float = 1.0
    prior_beta: float = 1.0
    margin_delta: float = 0.05
    decision_threshold: float = 0.95
    min_sample_size: int = 15
    max_sample_size: int = 60
    open_ended_pool_cap: int = 40
    wilson_confidence: float = 0.95

class ObsolescenceConfig(BaseModel):
    min_clusters: int = 6
    bootstrap_samples: int = 1000
    hazard_models: List[str] = Field(default_factory=lambda: ["exponential", "weibull"])
    calibration_providers: List[str] = Field(default_factory=lambda: ["OpenAI", "Anthropic", "Google", "DeepSeek", "Meta", "Mistral"])
    walk_forward_train_ratio: float = 0.60

class ValuationPanelCell(BaseModel):
    cell_id: str
    tenor_days: int
    age_days: int
    successor_active: bool
    depth_liquidity: float
    conversion_rate: float

class ValuationConfig(BaseModel):
    discount_rate: float = 0.04
    basis_polynomial_degree: int = 2
    lsm_paths: int = 5000
    panel_replications: int = 20
    risk_aversions: List[float] = Field(default_factory=lambda: [0.0, 0.1, 0.25, 0.5])
    panel_cells: List[ValuationPanelCell] = Field(default_factory=lambda: [
        ValuationPanelCell(cell_id="cell_1_short_fresh", tenor_days=30, age_days=15, successor_active=False, depth_liquidity=0.05, conversion_rate=0.0),
        ValuationPanelCell(cell_id="cell_2_mid_maturing", tenor_days=90, age_days=90, successor_active=False, depth_liquidity=0.02, conversion_rate=0.0),
        ValuationPanelCell(cell_id="cell_3_shock_rollover", tenor_days=90, age_days=180, successor_active=True, depth_liquidity=0.01, conversion_rate=0.5),
        ValuationPanelCell(cell_id="cell_4_long_frozen", tenor_days=180, age_days=240, successor_active=True, depth_liquidity=0.005, conversion_rate=0.0),
        ValuationPanelCell(cell_id="cell_5_full_conversion", tenor_days=90, age_days=120, successor_active=True, depth_liquidity=0.03, conversion_rate=1.0)
    ])

class ClearingConfig(BaseModel):
    clearing_type: str = "uniform_clearing"
    platform_fee_bps: float = 25.0
    welfare_ratio_gate_min: float = 0.85
    holdout_wilson_confidence: float = 0.95

class SellerConfig(BaseModel):
    target_utilization: float = 0.85
    cannibalization_dampener: float = 0.80
    capacity_tiers: List[float] = Field(default_factory=lambda: [100.0, 500.0, 2000.0])

class AgentConfig(BaseModel):
    dev_corruption_seed: int = 42
    test_corruption_seed: int = 1337
    grounding_relative_tolerance: float = 0.02
    budget_usd_cap: float = 50.00
    sub_cap_ceiling_check_usd: float = 4.00

class ParityConfig(BaseModel):
    substitutability: SubstitutabilityConfig = Field(default_factory=SubstitutabilityConfig)
    obsolescence: ObsolescenceConfig = Field(default_factory=ObsolescenceConfig)
    valuation: ValuationConfig = Field(default_factory=ValuationConfig)
    clearing: ClearingConfig = Field(default_factory=ClearingConfig)
    seller: SellerConfig = Field(default_factory=SellerConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)

def get_config_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "config"

def load_substitutability_config(config_dir: Optional[Path] = None) -> SubstitutabilityConfig:
    p = (config_dir or get_config_dir()) / "substitutability.yaml"
    if p.exists():
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return SubstitutabilityConfig.model_validate(data)
    return SubstitutabilityConfig()

def load_obsolescence_config(config_dir: Optional[Path] = None) -> ObsolescenceConfig:
    p = (config_dir or get_config_dir()) / "obsolescence.yaml"
    if p.exists():
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return ObsolescenceConfig.model_validate(data)
    return ObsolescenceConfig()

def load_valuation_config(config_dir: Optional[Path] = None) -> ValuationConfig:
    p = (config_dir or get_config_dir()) / "valuation.yaml"
    if p.exists():
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return ValuationConfig.model_validate(data)
    return ValuationConfig()

def load_clearing_config(config_dir: Optional[Path] = None) -> ClearingConfig:
    p = (config_dir or get_config_dir()) / "clearing.yaml"
    if p.exists():
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return ClearingConfig.model_validate(data)
    return ClearingConfig()

def load_seller_config(config_dir: Optional[Path] = None) -> SellerConfig:
    p = (config_dir or get_config_dir()) / "seller.yaml"
    if p.exists():
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return SellerConfig.model_validate(data)
    return SellerConfig()

def load_agent_config(config_dir: Optional[Path] = None) -> AgentConfig:
    p = (config_dir or get_config_dir()) / "agent.yaml"
    if p.exists():
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return AgentConfig.model_validate(data)
    return AgentConfig()

def load_parity_config(config_dir: Optional[Path] = None) -> ParityConfig:
    cd = config_dir or get_config_dir()
    return ParityConfig(
        substitutability=load_substitutability_config(cd),
        obsolescence=load_obsolescence_config(cd),
        valuation=load_valuation_config(cd),
        clearing=load_clearing_config(cd),
        seller=load_seller_config(cd),
        agent=load_agent_config(cd)
    )
