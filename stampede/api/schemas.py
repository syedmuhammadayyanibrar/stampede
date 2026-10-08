from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from stampede.types import Quantity, Series, Notice

class UsageJsonInput(BaseModel):
    monthly_tokens: float
    growth_pct_per_month: float = 0.0
    daily_volatility_pct: float = 15.0
    notes: str = ""
    input_output_ratio: float = 3.0

class PromptCheck(BaseModel):
    check_type: str
    target: str

class PromptItem(BaseModel):
    text: str
    checks: Optional[List[PromptCheck]] = None

class WorkloadInputRequest(BaseModel):
    prompts: List[PromptItem]
    description: Optional[str] = None
    input_output_ratio: Optional[float] = None

class WorkloadGenerateRequest(BaseModel):
    description: str
    n: int = 10

class ConstraintsTextRequest(BaseModel):
    text: str

class StructuredConstraintItem(BaseModel):
    field: str
    value: Any
    is_hard: bool = True
    evidence_quote: str

class StructuredConstraints(BaseModel):
    excluded_providers: List[str] = Field(default_factory=list)
    allowed_models: List[str] = Field(default_factory=list)
    max_spend_usd: Optional[float] = None
    min_parity: Optional[float] = None
    min_tenor_days: Optional[int] = None
    max_tenor_days: Optional[int] = None
    max_prepay_pct: Optional[float] = None
    require_resale: bool = False
    require_conversion: bool = False
    max_provider_share: Optional[float] = None
    start_by_days: Optional[int] = None
    evidence_quotes: Dict[str, str] = Field(default_factory=dict)
    unparsed_remainder: str = ""

class QuoteParsed(BaseModel):
    id: str
    provider: str
    model_id: str
    list_price_in_per_mtok: float
    list_price_out_per_mtok: float
    discount_pct: float
    tenor_days: int
    size_tokens: float
    prepay_pct: float = 0.0
    start_in_days: int = 0
    resale_allowed: bool = True
    resale_fee_pct: float = 0.10
    conversion: str = "none"
    notes: str = ""
    evidence_quotes: Dict[str, str] = Field(default_factory=dict)

class QuotesTextRequest(BaseModel):
    text: str

class QuotesStructuredRequest(BaseModel):
    quotes: List[QuoteParsed]

class EstimateRequest(BaseModel):
    stages: List[str]
    incumbent: str
    candidates: List[str]

class RunRequest(BaseModel):
    stages: List[str]
    incumbent: str
    candidates: List[str]
    confirm_estimate: bool = False

class WhatIfRequest(BaseModel):
    successor_launch_day: Optional[int] = None
    price_cut_pct: Optional[float] = None
    depth: Optional[str] = None
    risk_aversion: Optional[float] = None
    conversion_fraction: Optional[float] = None
    growth_multiplier: Optional[float] = None
    plan_change_probability: Optional[float] = None
    excluded_providers: Optional[List[str]] = None
    discount_overrides: Optional[Dict[str, float]] = None
    theta0: Optional[float] = None
    horizon_days: Optional[int] = None
    sell_day: Optional[int] = None
    remaining_share: Optional[float] = None

class ExplainRequest(BaseModel):
    target: str

class SellerUpliftRequest(BaseModel):
    capacity_params: Dict[str, float]
    demand_params: Dict[str, float]
    committed_share: float = 0.70
    forecast_error: float = 0.20

class ErrorEnvelope(BaseModel):
    code: str
    message: str
    detail: Optional[Any] = None
