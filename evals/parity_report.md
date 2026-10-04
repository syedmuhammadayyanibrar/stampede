# Parity Quantitative Evaluation Report

- **Timestamp**: 2026-10-04 14:32:21 UTC
- **Total Gates**: 30
- **Passed**: 30
- **Failed**: 0
- **Inconclusive**: 0
- **Runtime**: 0.06 seconds

## Scorecard

| Gate | Metric Name | Direction | Threshold | Observed | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| G01 | `judge_accuracy_kappa` | >= | 0.7 score | 0.88 score | **PASS** |
| G02 | `judge_swap_flip_rate` | <= | 0.1 rate | 0.04 rate | **PASS** |
| G03 | `sequential_stopping_efficiency` | >= | 0.25 ratio | 0.4317 ratio | **PASS** |
| G04 | `holdout_calibration_brier` | <= | 0.15 score | 0.0411 score | **PASS** |
| G05 | `cost_ranking_monotonicity` | >= | 0.85 correlation | 0.9343 correlation | **PASS** |
| G06 | `effective_cost_ratio_mae` | <= | 0.08 error | 0.0097 error | **PASS** |
| G07 | `multi_turn_degradation_recall` | >= | 0.8 rate | 0.95 rate | **PASS** |
| G08 | `hazard_brier_90d` | <= | 0.18 score | 0.0772 score | **PASS** |
| G09 | `price_path_cone_coverage` | >= | 0.8 rate | 1.0 rate | **PASS** |
| G10 | `successor_timing_mae_days` | <= | 45.0 days | 8.21 days | **PASS** |
| G11 | `depreciation_ranking_spearman` | >= | 0.7 correlation | 0.9189 correlation | **PASS** |
| G12 | `obsolescence_premium_monotonicity` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G13 | `lsm_option_non_negativity` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G14 | `lsm_panel_stability_se` | <= | 0.02 dollars_per_m | 0.0003 dollars_per_m | **PASS** |
| G15 | `early_exercise_monotonicity` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G16 | `shapley_efficiency_residual` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G17 | `shapley_symmetry_parity` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G18 | `zopa_existence_identification_rate` | >= | 0.9 rate | 1.0 rate | **PASS** |
| G19 | `zopa_width_contraction_monotonicity` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G20 | `clearing_envy_freeness_rate` | >= | 0.95 rate | 1.0 rate | **PASS** |
| G21 | `market_welfare_uplift_ratio` | >= | 1.08 ratio | 4.0064 ratio | **PASS** |
| G22 | `secondary_spread_compression_50pct` | >= | 0.2 ratio | 0.45 ratio | **PASS** |
| G23 | `procurement_outperformance_vs_baseline` | >= | 0.05 ratio | 0.3357 ratio | **PASS** |
| G24 | `allocation_regret_ratio` | <= | 0.08 ratio | 0.0638 ratio | **PASS** |
| G25 | `downside_risk_p95_containment` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G26 | `provider_concentration_compliance` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G27 | `explanation_grounding_accuracy` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G28 | `corrupted_csv_header_repair_rate` | >= | 0.9 rate | 1.0 rate | **PASS** |
| G29 | `corrupted_csv_row_recovery_rate` | >= | 0.85 rate | 1.0 rate | **PASS** |
| G30 | `pipeline_offline_latency_seconds` | <= | 120.0 seconds | 0.0568 seconds | **PASS** |
