# Stampede Live Evaluation Report

- Timestamp: 2026-10-08 06:11:26 UTC
- Platform: Windows-11-10.0.26200-SP0 (AMD64 Family 25 Model 80 Stepping 0, AuthenticAMD)
- Python Version: 3.12.0
- Execution Duration: 1.44s
- Summary: 12/15 PASSED, 0 FAILED, 3 SKIPPED

## Gates Summary

| Gate ID | Metric Name | Target | Threshold | Observed | Status |
|---|---|:---:|:---:|:---:|:---:|
| L01 | whatif_exactness_recompute_max_diff | <= | 0.0 absolute_diff | 0.0 absolute_diff | **PASS** |
| L02 | whatif_p95_latency_seconds | <= | 2.0 seconds | 0.0675 seconds | **PASS** |
| L03 | provenance_coverage_of_numeric_leaves | >= | 1.0 ratio | 1.0 ratio | **PASS** |
| L04 | ungrounded_numeric_claims_count | <= | 0.0 count | 0.0 count | **PASS** |
| L05 | budget_safety_cap_violations | <= | 0.0 count | 0.0 count | **PASS** |
| L06 | privacy_sentinel_hits_after_wipe | <= | 0.0 count | 0.0 count | **PASS** |
| L07 | sse_resume_exactness_ratio | >= | 1.0 ratio | 1.0 ratio | **PASS** |
| L08 | live_vs_offline_decision_equivalence | >= | 1.0 ratio | 1.0 ratio | **PASS** |
| L09 | quote_fixtures_and_property_tests_pass_rate | >= | 1.0 ratio | 1.0 ratio | **PASS** |
| L10 | judge_adjust_interval_coverage_and_mae | >= | 0.85 ratio | 1.0 ratio | **PASS** |
| L11 | ingestion_fallback_silent_wrong_accept_rate | >= | 0.9 ratio | 0.0 ratio | **SKIPPED(no_key)** |
| L12 | constraint_extraction_field_f1 | >= | 0.9 score | 0.0 score | **SKIPPED(no_key)** |
| L13 | quote_email_extraction_field_f1 | >= | 0.85 score | 0.0 score | **SKIPPED(no_key)** |
| L14 | end_to_end_fake_models_cost_estimate_ratio | <= | 1.25 ratio | 0.0001 ratio | **PASS** |
| L15 | input_sensitivity_expected_direction_fraction | >= | 1.0 ratio | 1.0 ratio | **PASS** |
