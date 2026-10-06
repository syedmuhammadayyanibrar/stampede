# Curating Model Obsolescence and Price-Change Events

## Overview
This document specifies the data curation standards and protocol for historical AI model lifecycle events (releases, price cuts, deprecation notices, shutdowns) across frontier foundation model providers.

## Strict Empirical Verification Standard
In accordance with Parity honesty rules:
1. Every event must be sourced directly from an official provider announcement page, official API changelog, documentation archive, or verified Internet Archive Wayback Machine snapshot.
2. An exact verbatim quote (at most 25 words) from the source page must be recorded under `evidence_quote`.
3. No event may be synthesized, inferred, or recorded from training memory.
4. Dates must be recorded in ISO format (`YYYY-MM-DD`).

## Schema (`data/price_history/events.csv`)
- `event_id`: Unique identifier (e.g. `evt_openai_001`).
- `provider`: Foundation model organization (`OpenAI`, `Anthropic`, `Google`, `DeepSeek`, `Meta`, `Mistral`).
- `model_id`: Canonical API model string (e.g. `openai/gpt-4o`).
- `tier_slot`: Capacity tier classification (`frontier`, `standard`, `budget`).
- `event_type`: Event category (`release`, `price_change`, `deprecation_notice`, `shutdown`).
- `event_date`: Official date of event occurrence (`YYYY-MM-DD`).
- `input_price_per_mtok`: Nominal input token price per million after event.
- `output_price_per_mtok`: Nominal output token price per million after event.
- `successor_model_id`: ID of the superseding successor model if applicable.
- `source_url`: Full canonical URL of source announcement.
- `retrieved_on`: Date the source was fetched and verified.
- `evidence_quote`: Verbatim quote from announcement confirming date and price/release terms.
- `status`: Verification status (`verified`, `unverified`).

## Sufficiency Threshold for Gated Calibration
- **Requirement:** A minimum of 60 verified events across at least 4 distinct providers is strictly required before fitting gated hazard regressions or backtesting walk-forward models.
- **Current Curated State:** 23 verified events across 6 providers (`OpenAI`, `Anthropic`, `Google`, `DeepSeek`, `Meta`, `Mistral`).
- **Gating Status:** Because $23 < 60$, Module 2 gates G08–G11 are formally marked `SKIPPED(insufficient_data)`.
- **Downstream Fallback:** Contract valuation (Module 3) reports `params_source="assumed_v1"` and uses the calibrated v1 jump-diffusion parameters. Any preliminary parametric fits are labeled `exploratory, n=23, not gated`.
