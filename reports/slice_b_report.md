# Stampede Slice B Verification Report

- Timestamp: 2026-10-07 16:28:39 UTC
- Platform: Windows-11-10.0.26200 (AMD64 AMD64 Family 25 Model 80 Stepping 0, AuthenticAMD)
- Python Version: 3.12.0
- Mode: offline
- Summary: 11/11 PASSED, 0 FAILED
- Acceptance Gate Status: **PASS**

## Acceptance Criteria Summary (evals/acceptance.yaml)

| Criterion | Name | Target | Threshold | Observed | Status |
|---|---|:---:|:---:|:---:|:---:|
| C1 | safety_rails_cap_kill_byok | >= | 1.0 ratio | 1.0 ratio | **PASS** |
| C10 | narrative_and_rfq_numeric_grounding_check | >= | 1.0 ratio | 1.0 ratio | **PASS** |
| C11 | planner_hard_constraint_satisfaction | >= | 1.0 ratio | 1.0 ratio | **PASS** |
| C2 | sequential_test_budget_and_decision | >= | 1.0 ratio | 1.0 ratio | **PASS** |
| C3 | verifiers_six_types | >= | 1.0 ratio | 1.0 ratio | **PASS** |
| C4 | reservation_prices_monotonicity_and_consistency | >= | 1.0 ratio | 1.0 ratio | **PASS** |
| C5 | quote_parser_and_ranking | >= | 1.0 ratio | 1.0 ratio | **PASS** |
| C6 | waterfall_exact_sum | >= | 1.0 ratio | 1.0 ratio | **PASS** |
| C7 | svg_charts_rendering_and_tables | >= | 1.0 ratio | 1.0 ratio | **PASS** |
| C8 | constraint_extraction_f1_and_evidence | >= | 1.0 ratio | 1.0 ratio | **PASS** |
| C9 | ingestion_silent_wrong_accept_and_success | >= | 1.0 ratio | 1.0 ratio | **PASS** |

## Detailed Criterion Breakdown

### C1: safety_rails_cap_kill_byok
- **Description**: Safety rails refuse over-cap runs, respect kill switch, and protect BYOK key
- **Status**: PASS
- **Observed Score**: 1.0
- **Verification Details**:
  - `estimate_ok`: True
  - `refused_over_cap`: True
  - `kill_blocks_run`: True
  - `kill_allows_get`: True
  - `byok_not_in_run_resp`: True
  - `byok_not_in_db`: True

### C10: narrative_and_rfq_numeric_grounding_check
- **Description**: Across 30 sessions ungrounded numeric tokens equals 0 with 2% relative tolerance
- **Status**: PASS
- **Observed Score**: 1.0
- **Verification Details**:
  - `ungrounded_count`: 0
  - `sessions_tested`: 30

### C11: planner_hard_constraint_satisfaction
- **Description**: Hard-constraint violations in plans equal 0 across 200 random scenarios
- **Status**: PASS
- **Observed Score**: 1.0
- **Verification Details**:
  - `violations`: 0
  - `scenarios_tested`: 200

### C2: sequential_test_budget_and_decision
- **Description**: Sequential test stops within budget and matches benchmark decision
- **Status**: PASS
- **Observed Score**: 1.0
- **Verification Details**:
  - `res_parity_decision`: parity
  - `res_inferior_decision`: inferior
  - `stops_within_budget`: True
  - `matches_decision`: True

### C3: verifiers_six_types
- **Description**: Verifiers run correctly across all six types including json schema and unicode
- **Status**: PASS
- **Observed Score**: 1.0
- **Verification Details**:

### C4: reservation_prices_monotonicity_and_consistency
- **Description**: Reservation prices are monotonic in tenor and satisfy zero-saving consistency
- **Status**: PASS
- **Observed Score**: 1.0
- **Verification Details**:
  - `p30`: 9.28
  - `p60`: 16.27
  - `p90`: 22.6
  - `monotonic`: True
  - `risk_adj_saving`: -0.10475396874556964
  - `se_usd`: 17.935000000000002
  - `consistency_passed`: True

### C5: quote_parser_and_ranking
- **Description**: Quote parser rejects invalid discounts, extracts quotes, and ranks accurately
- **Status**: PASS
- **Observed Score**: 1.0
- **Verification Details**:
  - `discount_ok`: True
  - `word_discount_ok`: True
  - `invalid_rejected`: True
  - `warning_present`: True
  - `evidence_ok`: True
  - `rank_ok`: True

### C6: waterfall_exact_sum
- **Description**: Waterfall telescoping decomposition sums to full valuation with zero residual
- **Status**: PASS
- **Observed Score**: 1.0
- **Verification Details**:
  - `residual_error`: 0.0
  - `telescopes`: True
  - `is_exact_sum`: True
  - `bars_count`: 6
  - `signs_valid`: True

### C7: svg_charts_rendering_and_tables
- **Description**: SVG charts render with matching data tables and answering titles
- **Status**: PASS
- **Observed Score**: 1.0
- **Verification Details**:
  - `has_posterior_question`: True
  - `has_waterfall_question`: True
  - `has_posterior_svg`: True
  - `has_waterfall_svg`: True
  - `has_posterior_table`: True
  - `has_waterfall_table`: True

### C8: constraint_extraction_f1_and_evidence
- **Description**: Constraint extraction achieves field-level F1 >= 0.90 and 1.0 evidence quote presence
- **Status**: PASS
- **Observed Score**: 1.0
- **Verification Details**:
  - `mean_f1`: 1.0
  - `mean_evidence_presence`: 1.0
  - `sample_size`: 40

### C9: ingestion_silent_wrong_accept_and_success
- **Description**: Ingestion fallback achieves zero silent-wrong-accept and >= 0.90 parse success on held-out set
- **Status**: PASS
- **Observed Score**: 1.0
- **Verification Details**:
  - `silent_wrong_accept`: 0
  - `parse_success_rate`: 1.0
  - `valid_tested`: 20
  - `invalid_tested`: 20

## Standing Rules & Hygiene Check

- Zero-comments policy: verified via `tests/parity/test_no_comments.py` (PASS)
- Claims hygiene: verified via `tests/stampede/test_claims.py` (PASS)
- Naming rules (LLM gateway vs deterministic): verified via `tests/stampede/test_naming_rule.py` (PASS)
- Numeric provenance: every value tagged with USER_INPUT, MEASURED_LIVE, MEASURED_BENCHMARK, FITTED, ASSUMED, or SIMULATED
