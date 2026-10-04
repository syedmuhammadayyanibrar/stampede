from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np

@dataclass(frozen=True)
class BuyerProfile:
    buyer_id: str
    tier: str
    daily_volume_tokens_m: float
    primary_archetypes: List[str]
    monthly_budget_usd: float
    risk_aversion: float
    excluded_providers: List[str] = field(default_factory=list)
    current_model: str = "openai/gpt-4o"

@dataclass(frozen=True)
class SellerProfile:
    seller_id: str
    provider: str
    model_family: str
    monthly_capacity_m: float
    unit_cost_usd_per_m: float
    supports_conversion: bool
    base_spread: float

def generate_standard_buyer_profiles() -> List[BuyerProfile]:
    return [
        BuyerProfile(
            buyer_id="buyer_startup_voice",
            tier="startup",
            daily_volume_tokens_m=2.5,
            primary_archetypes=["classification", "structured_extraction"],
            monthly_budget_usd=12000.0,
            risk_aversion=0.10,
            excluded_providers=[],
            current_model="openai/gpt-4o"
        ),
        BuyerProfile(
            buyer_id="buyer_scaleup_agent",
            tier="scale_up",
            daily_volume_tokens_m=15.0,
            primary_archetypes=["code_generation", "reasoning_math", "rag_qa"],
            monthly_budget_usd=85000.0,
            risk_aversion=0.25,
            excluded_providers=["DeepSeek"],
            current_model="anthropic/claude-3.5-sonnet"
        ),
        BuyerProfile(
            buyer_id="buyer_enterprise_global",
            tier="enterprise",
            daily_volume_tokens_m=80.0,
            primary_archetypes=["summarization", "translation", "rag_qa"],
            monthly_budget_usd=450000.0,
            risk_aversion=0.40,
            excluded_providers=[],
            current_model="openai/gpt-4o"
        )
    ]

def generate_standard_seller_profiles() -> List[SellerProfile]:
    return [
        SellerProfile(
            seller_id="seller_openai_host",
            provider="OpenAI",
            model_family="openai/gpt-4o",
            monthly_capacity_m=500.0,
            unit_cost_usd_per_m=2.50,
            supports_conversion=True,
            base_spread=0.06
        ),
        SellerProfile(
            seller_id="seller_anthropic_host",
            provider="Anthropic",
            model_family="anthropic/claude-3.5-sonnet",
            monthly_capacity_m=350.0,
            unit_cost_usd_per_m=2.10,
            supports_conversion=True,
            base_spread=0.05
        ),
        SellerProfile(
            seller_id="seller_deepseek_host",
            provider="DeepSeek",
            model_family="deepseek/deepseek-chat",
            monthly_capacity_m=800.0,
            unit_cost_usd_per_m=0.20,
            supports_conversion=False,
            base_spread=0.08
        )
    ]
