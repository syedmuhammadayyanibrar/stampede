from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class Provenance(str, Enum):
    USER_INPUT = "USER_INPUT"
    MEASURED_LIVE = "MEASURED_LIVE"
    MEASURED_BENCHMARK = "MEASURED_BENCHMARK"
    FITTED = "FITTED"
    ASSUMED = "ASSUMED"
    SIMULATED = "SIMULATED"

import uuid

class Quantity(BaseModel):
    id: str = Field(default_factory=lambda: f"qty_{uuid.uuid4().hex[:8]}")
    value: float
    lo90: Optional[float] = None
    hi90: Optional[float] = None
    n: Optional[int] = None
    unit: str = "usd"
    provenance: Provenance
    source: str = "engine"
    note: Optional[str] = None

class Series(BaseModel):
    name: str
    unit: str
    provenance: Provenance
    source: str
    values: List[float]
    lo: Optional[List[float]] = None
    hi: Optional[List[float]] = None

class Notice(BaseModel):
    code: str
    severity: str
    text: str

class StandingNotices:
    SIMULATED_EXIT_POOL = Notice(
        code="SIMULATED_EXIT_POOL",
        severity="info",
        text="Exit route secondary liquidity pool is synthetic and simulated."
    )
    ASSUMED_SELLER_PARAMS = Notice(
        code="ASSUMED_SELLER_PARAMS",
        severity="info",
        text="Provider seller parameters and cost structures are assumed scenario baselines."
    )
    THIN_HAZARD_DATA = Notice(
        code="THIN_HAZARD_DATA",
        severity="warning",
        text="Price hazard and obsolescence calculations are based on curated historical events (n=23)."
    )
    OPENROUTER_PROXY_PRICES = Notice(
        code="OPENROUTER_PROXY_PRICES",
        severity="info",
        text="OpenRouter prices are utilized as a real-time proxy for provider-direct contract execution."
    )
    JUDGE_ERROR_TRANSFER = Notice(
        code="JUDGE_ERROR_TRANSFER",
        severity="info",
        text="Judge error rates are assumed to transfer from verified benchmark distributions to user workloads."
    )
    PARITY_RELATIVE_TO_INCUMBENT = Notice(
        code="PARITY_RELATIVE_TO_INCUMBENT",
        severity="info",
        text="Substitutability quality in judged mode is evaluated relative to the incumbent baseline."
    )
    VALUATION_SOURCE = Notice(
        code="VALUATION_SOURCE",
        severity="info",
        text="Contract valuation parameter source is assumed_v1."
    )
    OPENROUTER_ROUTING = Notice(
        code="OPENROUTER_ROUTING",
        severity="info",
        text="User prompts are transmitted to selected model providers via OpenRouter."
    )
