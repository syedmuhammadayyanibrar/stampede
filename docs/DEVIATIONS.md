# Parity Specification Deviations & Sign-Off Log

## DEV-001: Module 2 Sample Size & G08-G11 Gating
- **Item**: Price Trajectory & Obsolescence Hazard Estimation
- **Spec Requirement**: Minimum 60 verified price-cut / deprecation events across >= 4 providers for full parametric hazard gating.
- **Observed**: Curated verified dataset `data/price_history/events.csv` contains $n=23$ events across 6 providers (DeepSeek, OpenAI, Anthropic, Google, Meta, Mistral).
- **Resolution**: Under Touchmark Parity spec Section 1.4, Module 2 gates G08-G11 are reported as `SKIPPED(insufficient_data)` on formal evaluation. Module 3 operates with `params_source: "assumed_v1"`. The fitted hazard parameters are marked `"exploratory, n=23, not gated"` in `data/parity/obsolescence_curves.json`.
- **Sign-off Status**: PENDING USER SIGN-OFF.

## DEV-002: Archetype Verification Protocol
- **Item**: Module 1 Substitutability Matrix
- **Spec Requirement**: 8 evaluation archetypes (`json_extraction`, `text_to_sql`, `arithmetic_reasoning`, `ticket_classification`, `constraint_rewrite`, `grounded_qa`, `summarization`, `support_reply`).
- **Clarification**: Programmatic unit verifiers are used exclusively for objective, deterministic archetypes (JSON schema conformity, SQL parse trees and execution invariance, arithmetic numerical verification, exact ticket taxonomy matching, constraint rewrite rule adherence, and citation-span grounded QA). "Mathematical proofs" and "translation" claims have been removed from deterministic verification. Subjective archetypes (`summarization`, `support_reply`) are explicitly scored by LLM judges via `parity/gateway.py`.
- **Metrics**: Judge Cohen's kappa $\kappa = 0.8142 \ge 0.70$, swap flip rate $2.99\% \le 10.0\%$.
- **Sign-off Status**: PENDING USER SIGN-OFF.

## DEV-003: Extra Components Labeled "Extra, Not Gated"
- **Item**: Provider Concentration Limit (G26) and Multi-Turn Degradation (G07)
- **Status**: Retained in code and data artifacts under `"extra_not_gated"` payloads, omitted from headline market welfare claims.
- **Sign-off Status**: PENDING USER SIGN-OFF.
