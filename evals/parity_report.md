# Parity Quantitative Evaluation Report

- **Timestamp**: 2026-10-10 13:08:57 UTC
- **Total Gates**: 30
- **Passed**: 26
- **Failed**: 0
- **Skipped**: 4
- **Inconclusive**: 0
- **Runtime**: 0.03 seconds

## Scorecard

| Gate | Metric Name | Direction | Threshold | Observed | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| G01 | `judge_accuracy_kappa` | >= | 0.7 score | 0.8142 score | **PASS** |
| G02 | `judge_swap_flip_rate` | <= | 0.1 rate | 0.0299 rate | **PASS** |
| G03 | `sequential_stopping_efficiency` | >= | 0.25 ratio | 0.3788 ratio | **PASS** |
| G04 | `holdout_calibration_brier` | <= | 0.15 score | 0.0572 score | **PASS** |
| G05 | `cost_ranking_monotonicity` | >= | 0.85 correlation | 0.9593 correlation | **PASS** |
| G06 | `effective_cost_ratio_mae` | <= | 0.08 error | 0.0083 error | **PASS** |
| G07 | `multi_turn_degradation_recall` | >= | 0.8 rate | 0.95 rate | **PASS** |
| G08 | `hazard_brier_90d` | <= | 0.18 score | 0.0772 score | **INCONCLUSIVE** |
| G09 | `price_path_cone_coverage` | >= | 0.8 rate | 1.0 rate | **INCONCLUSIVE** |
| G10 | `successor_timing_mae_days` | <= | 45.0 days | 8.21 days | **INCONCLUSIVE** |
| G11 | `depreciation_ranking_spearman` | >= | 0.7 correlation | 0.9189 correlation | **INCONCLUSIVE** |
| G12 | `obsolescence_premium_monotonicity` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G13 | `lsm_option_non_negativity` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G14 | `lsm_panel_stability_se` | <= | 0.02 dollars_per_m | 0.0003 dollars_per_m | **PASS** |
| G15 | `early_exercise_monotonicity` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G16 | `shapley_efficiency_residual` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G17 | `shapley_symmetry_parity` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G18 | `zopa_existence_identification_rate` | >= | 0.9 rate | 1.0 rate | **PASS** |
| G19 | `zopa_width_contraction_monotonicity` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G20 | `clearing_envy_freeness_rate` | >= | 0.95 rate | 1.0 rate | **PASS** |
| G21 | `market_welfare_uplift_ratio` | >= | 1.08 ratio | 1.1809 ratio | **PASS** |
| G22 | `secondary_spread_compression_50pct` | >= | 0.2 ratio | 0.45 ratio | **PASS** |
| G23 | `procurement_outperformance_vs_baseline` | >= | 0.05 ratio | 0.093 ratio | **PASS** |
| G24 | `allocation_regret_ratio` | <= | 0.08 ratio | 0.0638 ratio | **PASS** |
| G25 | `downside_risk_p95_containment` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G26 | `provider_concentration_compliance` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G27 | `explanation_grounding_accuracy` | >= | 1.0 binary | 1.0 binary | **PASS** |
| G28 | `corrupted_csv_header_repair_rate` | >= | 0.9 rate | 1.0 rate | **PASS** |
| G29 | `corrupted_csv_row_recovery_rate` | >= | 0.85 rate | 1.0 rate | **PASS** |
| G30 | `pipeline_offline_latency_seconds` | <= | 120.0 seconds | 0.0321 seconds | **PASS** |
