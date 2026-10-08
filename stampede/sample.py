import json
from pathlib import Path
from typing import Dict, List, Any
from stampede.api.schemas import PromptItem, PromptCheck, QuoteParsed
from stampede.types import Quantity, Provenance, Notice

SAMPLE_USAGE_DATA = {
    "monthly_tokens": 45.0,
    "growth_pct_per_month": 6.5,
    "daily_volatility_pct": 14.0,
    "notes": "European customer onboarding expanding in Month 2 by +30%",
    "input_output_ratio": 3.0
}

SAMPLE_QUOTES = [
    QuoteParsed(
        id="sample_quote_1",
        provider="OpenAI",
        model_id="openai/gpt-4o",
        list_price_in_per_mtok=5.00,
        list_price_out_per_mtok=15.00,
        discount_pct=18.0,
        tenor_days=90,
        size_tokens=60.0,
        prepay_pct=25.0,
        start_in_days=0,
        resale_allowed=True,
        resale_fee_pct=0.10,
        conversion="par_to_successor",
        notes="Illustrative enterprise discount quote",
        evidence_quotes={"discount_pct": "18.0% enterprise commitment discount"}
    ),
    QuoteParsed(
        id="sample_quote_2",
        provider="Anthropic",
        model_id="anthropic/claude-3.5-sonnet",
        list_price_in_per_mtok=3.00,
        list_price_out_per_mtok=15.00,
        discount_pct=22.0,
        tenor_days=90,
        size_tokens=40.0,
        prepay_pct=0.0,
        start_in_days=0,
        resale_allowed=True,
        resale_fee_pct=0.15,
        conversion="best_in_class",
        notes="Illustrative enterprise tier quote",
        evidence_quotes={"discount_pct": "22.0% volume tier discount"}
    ),
    QuoteParsed(
        id="sample_quote_3",
        provider="DeepSeek",
        model_id="deepseek/deepseek-chat",
        list_price_in_per_mtok=0.14,
        list_price_out_per_mtok=0.28,
        discount_pct=30.0,
        tenor_days=60,
        size_tokens=30.0,
        prepay_pct=50.0,
        start_in_days=0,
        resale_allowed=False,
        resale_fee_pct=0.0,
        conversion="none",
        notes="Illustrative discounted cluster reservation",
        evidence_quotes={"discount_pct": "30% upfront commitment discount"}
    )
]

def load_sample_prompts() -> List[PromptItem]:
    prompts_path = Path("data/parity/prompts.json")
    items = []
    if prompts_path.exists():
        with open(prompts_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            verifiable = [p for p in raw if p.get("archetype") in ("json_extraction", "ticket_classification")]
            for p in verifiable[:24]:
                items.append(
                    PromptItem(
                        text=p.get("prompt", "Extract JSON fields"),
                        checks=[PromptCheck(check_type="must_contain", target="{")]
                    )
                )
    if not items:
        for i in range(1, 25):
            items.append(
                PromptItem(
                    text=f"Extract structured ticket JSON for case #{i}: user inquiry regarding API latency",
                    checks=[PromptCheck(check_type="must_contain", target="{")]
                )
            )
    return items

def get_sample_replay_notice() -> Notice:
    return Notice(
        code="REPLAYED_BENCHMARK_SAMPLE",
        severity="info",
        text="Replayed from stored benchmark outputs; the sequential test and every downstream computation run live."
    )
