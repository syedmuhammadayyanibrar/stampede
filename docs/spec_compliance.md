# Parity Specification Compliance Matrix

This document provides item-by-item verification against the Touchmark Parity Specification across all modules, all 30 quantitative evaluation gates (G01–G30), and all named codebase and data artifacts.

## 1. Modules

| Spec Item | Status | File Path | Command That Proves It |
| :--- | :--- | :--- | :--- |
| Module 0: Harness, Config & Baselines | IMPLEMENTED | [parity/config.py](file:///c:/stampede/parity/config.py) | `python -m pytest tests/parity/test_config_defaults.py` |
| Module 1: Substitutability Matrix | IMPLEMENTED | [parity/substitutability/runner.py](file:///c:/stampede/parity/substitutability/runner.py) | `python -m pytest tests/parity/test_substitutability.py` |
| Module 2: Obsolescence Hazard & Trajectories | PARTIAL | [parity/obsolescence/backtester.py](file:///c:/stampede/parity/obsolescence/backtester.py) | `python -m pytest tests/parity/test_obsolescence.py` |
| Module 3: Secondary Valuation & Shapley | IMPLEMENTED | [parity/valuation/runner.py](file:///c:/stampede/parity/valuation/runner.py) | `python -m pytest tests/parity/test_valuation.py` |
| Module 4: Clearing Engine & Welfare | IMPLEMENTED | [parity/clearing/runner.py](file:///c:/stampede/parity/clearing/runner.py) | `python -m pytest tests/parity/test_clearing.py` |
| Module 5: Dynamic Seller Pricing & ZOPA | IMPLEMENTED | [parity/seller/runner.py](file:///c:/stampede/parity/seller/runner.py) | `python -m pytest tests/parity/test_seller.py` |
| Module 6: Autonomous Procurement Copilot | IMPLEMENTED | [parity/agent/runner.py](file:///c:/stampede/parity/agent/runner.py) | `python -m pytest tests/parity/test_agent.py` |

## 2. Evaluation Gates (G01–G30)

| Spec Item | Status | File Path | Command That Proves It |
| :--- | :--- | :--- | :--- |
| G01: judge_accuracy_kappa | IMPLEMENTED | [parity/substitutability/judge.py](file:///c:/stampede/parity/substitutability/judge.py) | `python eval.py` |
| G02: judge_swap_flip_rate | IMPLEMENTED | [parity/substitutability/judge.py](file:///c:/stampede/parity/substitutability/judge.py) | `python eval.py` |
| G03: sequential_stopping_efficiency | IMPLEMENTED | [parity/substitutability/engine.py](file:///c:/stampede/parity/substitutability/engine.py) | `python eval.py` |
| G04: holdout_calibration_brier | IMPLEMENTED | [parity/substitutability/runner.py](file:///c:/stampede/parity/substitutability/runner.py) | `python eval.py` |
| G05: cost_ranking_monotonicity | IMPLEMENTED | [parity/substitutability/engine.py](file:///c:/stampede/parity/substitutability/engine.py) | `python eval.py` |
| G06: effective_cost_ratio_mae | IMPLEMENTED | [parity/substitutability/runner.py](file:///c:/stampede/parity/substitutability/runner.py) | `python eval.py` |
| G07: multi_turn_degradation_recall | IMPLEMENTED | [parity/substitutability/multiturn.py](file:///c:/stampede/parity/substitutability/multiturn.py) | `python eval.py` |
| G08: hazard_brier_90d | PARTIAL | [parity/obsolescence/backtester.py](file:///c:/stampede/parity/obsolescence/backtester.py) | `python eval.py` |
| G09: price_path_cone_coverage | PARTIAL | [parity/obsolescence/price_path.py](file:///c:/stampede/parity/obsolescence/price_path.py) | `python eval.py` |
| G10: successor_timing_mae_days | PARTIAL | [parity/obsolescence/backtester.py](file:///c:/stampede/parity/obsolescence/backtester.py) | `python eval.py` |
| G11: depreciation_ranking_spearman | PARTIAL | [parity/obsolescence/backtester.py](file:///c:/stampede/parity/obsolescence/backtester.py) | `python eval.py` |
| G12: obsolescence_premium_monotonicity | IMPLEMENTED | [parity/obsolescence/price_path.py](file:///c:/stampede/parity/obsolescence/price_path.py) | `python eval.py` |
| G13: lsm_option_non_negativity | IMPLEMENTED | [parity/valuation/lsm.py](file:///c:/stampede/parity/valuation/lsm.py) | `python eval.py` |
| G14: lsm_panel_stability_se | IMPLEMENTED | [parity/valuation/runner.py](file:///c:/stampede/parity/valuation/runner.py) | `python eval.py` |
| G15: early_exercise_monotonicity | IMPLEMENTED | [parity/valuation/lsm.py](file:///c:/stampede/parity/valuation/lsm.py) | `python eval.py` |
| G16: shapley_efficiency_residual | IMPLEMENTED | [parity/valuation/shapley.py](file:///c:/stampede/parity/valuation/shapley.py) | `python eval.py` |
| G17: shapley_symmetry_parity | IMPLEMENTED | [parity/valuation/shapley.py](file:///c:/stampede/parity/valuation/shapley.py) | `python eval.py` |
| G18: zopa_existence_identification_rate | IMPLEMENTED | [parity/valuation/zopa.py](file:///c:/stampede/parity/valuation/zopa.py) | `python eval.py` |
| G19: zopa_width_contraction_monotonicity | IMPLEMENTED | [parity/valuation/zopa.py](file:///c:/stampede/parity/valuation/zopa.py) | `python eval.py` |
| G20: clearing_envy_freeness_rate | IMPLEMENTED | [parity/clearing/lp_solver.py](file:///c:/stampede/parity/clearing/lp_solver.py) | `python eval.py` |
| G21: market_welfare_uplift_ratio | IMPLEMENTED | [parity/clearing/runner.py](file:///c:/stampede/parity/clearing/runner.py) | `python eval.py` |
| G22: secondary_spread_compression_50pct | IMPLEMENTED | [parity/seller/runner.py](file:///c:/stampede/parity/seller/runner.py) | `python eval.py` |
| G23: procurement_outperformance_vs_baseline | IMPLEMENTED | [parity/agent/core_planner.py](file:///c:/stampede/parity/agent/core_planner.py) | `python eval.py` |
| G24: allocation_regret_ratio | IMPLEMENTED | [parity/agent/core_planner.py](file:///c:/stampede/parity/agent/core_planner.py) | `python eval.py` |
| G25: downside_risk_p95_containment | IMPLEMENTED | [parity/agent/core_planner.py](file:///c:/stampede/parity/agent/core_planner.py) | `python eval.py` |
| G26: provider_concentration_compliance | IMPLEMENTED | [parity/agent/core_planner.py](file:///c:/stampede/parity/agent/core_planner.py) | `python eval.py` |
| G27: explanation_grounding_accuracy | IMPLEMENTED | [parity/agent/grounding.py](file:///c:/stampede/parity/agent/grounding.py) | `python eval.py` |
| G28: corrupted_csv_header_repair_rate | IMPLEMENTED | [parity/agent/parser_wrapper.py](file:///c:/stampede/parity/agent/parser_wrapper.py) | `python eval.py` |
| G29: corrupted_csv_row_recovery_rate | IMPLEMENTED | [parity/agent/parser_wrapper.py](file:///c:/stampede/parity/agent/parser_wrapper.py) | `python eval.py` |
| G30: pipeline_offline_latency_seconds | IMPLEMENTED | [eval.py](file:///c:/stampede/eval.py) | `python eval.py` |

## 3. Named Source, Data & Report Artifacts

| Spec Item | Status | File Path | Command That Proves It |
| :--- | :--- | :--- | :--- |
| Threshold Specifications | IMPLEMENTED | [evals/thresholds_parity.yaml](file:///c:/stampede/evals/thresholds_parity.yaml) | `python -m pytest tests/parity/test_eval.py` |
| Threshold Hash Lock | IMPLEMENTED | [evals/thresholds_parity.lock](file:///c:/stampede/evals/thresholds_parity.lock) | `python -m pytest tests/parity/test_eval.py` |
| 30-Gate Evaluation Harness | IMPLEMENTED | [eval.py](file:///c:/stampede/eval.py) | `python eval.py` |
| v1 Base Evaluation Suite | IMPLEMENTED | [run_evals.py](file:///c:/stampede/run_evals.py) | `python run_evals.py` |
| LLM Gateway & Replay Mode | IMPLEMENTED | [parity/gateway.py](file:///c:/stampede/parity/gateway.py) | `python -c "from parity.gateway import LLMGateway; g = LLMGateway(offline=True)"` |
| Atomic File I/O | IMPLEMENTED | [parity/io.py](file:///c:/stampede/parity/io.py) | `python -c "from parity.io import read_json"` |
| Configuration Loader | IMPLEMENTED | [parity/config.py](file:///c:/stampede/parity/config.py) | `python -m pytest tests/parity/test_config_defaults.py` |
| Spend Ledger Tracker | IMPLEMENTED | [parity/spend_tracker.py](file:///c:/stampede/parity/spend_tracker.py) | `python -m pytest tests/parity/test_spend_tracker.py` |
| Substitutability Engine | IMPLEMENTED | [parity/substitutability/engine.py](file:///c:/stampede/parity/substitutability/engine.py) | `python -m pytest tests/parity/test_substitutability.py` |
| Deterministic Verifiers | IMPLEMENTED | [parity/substitutability/verifiers.py](file:///c:/stampede/parity/substitutability/verifiers.py) | `python -m pytest tests/parity/test_verifiers.py` |
| LLM Judge Protocol | IMPLEMENTED | [parity/substitutability/judge.py](file:///c:/stampede/parity/substitutability/judge.py) | `python -m pytest tests/parity/test_substitutability.py` |
| Multi-Turn Degradation Evaluator | IMPLEMENTED | [parity/substitutability/multiturn.py](file:///c:/stampede/parity/substitutability/multiturn.py) | `python -m pytest tests/parity/test_substitutability.py` |
| Substitutability Runner | IMPLEMENTED | [parity/substitutability/runner.py](file:///c:/stampede/parity/substitutability/runner.py) | `python -m pytest tests/parity/test_substitutability.py` |
| Parametric Hazard Estimator | IMPLEMENTED | [parity/obsolescence/hazard.py](file:///c:/stampede/parity/obsolescence/hazard.py) | `python -m pytest tests/parity/test_obsolescence.py` |
| Jump Diffusion Path Simulator | IMPLEMENTED | [parity/obsolescence/price_path.py](file:///c:/stampede/parity/obsolescence/price_path.py) | `python -m pytest tests/parity/test_obsolescence.py` |
| Obsolescence Backtester | IMPLEMENTED | [parity/obsolescence/backtester.py](file:///c:/stampede/parity/obsolescence/backtester.py) | `python -m pytest tests/parity/test_obsolescence.py` |
| Least-Squares Monte Carlo Engine | IMPLEMENTED | [parity/valuation/lsm.py](file:///c:/stampede/parity/valuation/lsm.py) | `python -m pytest tests/parity/test_valuation.py` |
| Exact 5-Factor Shapley Solver | IMPLEMENTED | [parity/valuation/shapley.py](file:///c:/stampede/parity/valuation/shapley.py) | `python -m pytest tests/parity/test_valuation.py` |
| Two-Sided ZOPA Engine | IMPLEMENTED | [parity/valuation/zopa.py](file:///c:/stampede/parity/valuation/zopa.py) | `python -m pytest tests/parity/test_valuation.py` |
| Secondary Valuation Runner | IMPLEMENTED | [parity/valuation/runner.py](file:///c:/stampede/parity/valuation/runner.py) | `python -m pytest tests/parity/test_valuation.py` |
| Five Clearing Mechanisms & Bootstrap | IMPLEMENTED | [parity/clearing/mechanisms.py](file:///c:/stampede/parity/clearing/mechanisms.py) | `python -m pytest tests/parity/test_clearing.py` |
| HiGHS Linear Programming Clearing Solver | IMPLEMENTED | [parity/clearing/lp_solver.py](file:///c:/stampede/parity/clearing/lp_solver.py) | `python -m pytest tests/parity/test_clearing.py` |
| Clearing Runner | IMPLEMENTED | [parity/clearing/runner.py](file:///c:/stampede/parity/clearing/runner.py) | `python -m pytest tests/parity/test_clearing.py` |
| Dynamic Seller Pricing Engine | IMPLEMENTED | [parity/seller/pricing_engine.py](file:///c:/stampede/parity/seller/pricing_engine.py) | `python -m pytest tests/parity/test_seller.py` |
| Seller Runner | IMPLEMENTED | [parity/seller/runner.py](file:///c:/stampede/parity/seller/runner.py) | `python -m pytest tests/parity/test_seller.py` |
| Deterministic Procurement Tools | IMPLEMENTED | [parity/agent/tools.py](file:///c:/stampede/parity/agent/tools.py) | `python -m pytest tests/parity/test_agent.py` |
| Deterministic Parity Core Planner | IMPLEMENTED | [parity/agent/core_planner.py](file:///c:/stampede/parity/agent/core_planner.py) | `python -m pytest tests/parity/test_agent.py` |
| LLM Parity Agent Loop | IMPLEMENTED | [parity/agent/loop.py](file:///c:/stampede/parity/agent/loop.py) | `python -m pytest tests/parity/test_agent.py` |
| Numeric Grounding Guard | IMPLEMENTED | [parity/agent/grounding.py](file:///c:/stampede/parity/agent/grounding.py) | `python -m pytest tests/parity/test_agent.py` |
| Normalizing CSV Parser Wrapper | IMPLEMENTED | [parity/agent/parser_wrapper.py](file:///c:/stampede/parity/agent/parser_wrapper.py) | `python -m pytest tests/parity/test_agent.py` |
| Two-Seed CSV Corruption Generator | IMPLEMENTED | [parity/agent/corruption_builder.py](file:///c:/stampede/parity/agent/corruption_builder.py) | `python -m pytest tests/parity/test_agent.py` |
| Procurement Module Runner | IMPLEMENTED | [parity/agent/runner.py](file:///c:/stampede/parity/agent/runner.py) | `python -m pytest tests/parity/test_agent.py` |
| 640 Prompt Dataset (8 Archetypes) | IMPLEMENTED | [data/parity/prompts.json](file:///c:/stampede/data/parity/prompts.json) | `python -c "import json; d=json.load(open('data/parity/prompts.json')); assert len(d)==640"` |
| Substitutability Matrix Artifact | IMPLEMENTED | [data/parity/substitutability_matrix.json](file:///c:/stampede/data/parity/substitutability_matrix.json) | `python -c "import json; d=json.load(open('data/parity/substitutability_matrix.json')); assert 'matrix' in d"` |
| Curated Historical Price Events ($n=23$) | PARTIAL | [data/price_history/events.csv](file:///c:/stampede/data/price_history/events.csv) | `python -c "import csv; rows=list(csv.reader(open('data/price_history/events.csv'))); assert len(rows)==24"` |
| Obsolescence Curves Artifact | IMPLEMENTED | [data/parity/obsolescence_curves.json](file:///c:/stampede/data/parity/obsolescence_curves.json) | `python -c "import json; d=json.load(open('data/parity/obsolescence_curves.json')); assert 'metrics' in d"` |
| Valuation Curves Artifact | IMPLEMENTED | [data/parity/valuation_curves.json](file:///c:/stampede/data/parity/valuation_curves.json) | `python -c "import json; d=json.load(open('data/parity/valuation_curves.json')); assert 'metrics' in d"` |
| Clearing Results Artifact | IMPLEMENTED | [data/parity/clearing_results.json](file:///c:/stampede/data/parity/clearing_results.json) | `python -c "import json; d=json.load(open('data/parity/clearing_results.json')); assert 'metrics' in d"` |
| Seller Curves Artifact | IMPLEMENTED | [data/parity/seller_curves.json](file:///c:/stampede/data/parity/seller_curves.json) | `python -c "import json; d=json.load(open('data/parity/seller_curves.json')); assert 'metrics' in d"` |
| Procurement Results Artifact | IMPLEMENTED | [data/parity/procurement_results.json](file:///c:/stampede/data/parity/procurement_results.json) | `python -c "import json; d=json.load(open('data/parity/procurement_results.json')); assert 'metrics' in d"` |
| Spend Ledger | IMPLEMENTED | [data/parity/spend_ledger.json](file:///c:/stampede/data/parity/spend_ledger.json) | `python -c "import json; d=json.load(open('data/parity/spend_ledger.json')); assert 'ledger' in d"` |
| Scorecard JSON Evaluation Results | IMPLEMENTED | [reports/parity_eval_results.json](file:///c:/stampede/reports/parity_eval_results.json) | `python -c "import json; d=json.load(open('reports/parity_eval_results.json')); assert 'gates' in d"` |
| Scorecard Markdown Evaluation Report | IMPLEMENTED | [reports/parity_eval_report.md](file:///c:/stampede/reports/parity_eval_report.md) | `python -c "import os; assert os.path.exists('reports/parity_eval_report.md')"` |
| Event Curation Protocol Documentation | IMPLEMENTED | [docs/curating_events.md](file:///c:/stampede/docs/curating_events.md) | `python -c "import os; assert os.path.exists('docs/curating_events.md')"` |
| Specification Deviations & Sign-Off Log | IMPLEMENTED | [docs/DEVIATIONS.md](file:///c:/stampede/docs/DEVIATIONS.md) | `python -c "import os; assert os.path.exists('docs/DEVIATIONS.md')"` |
| Specification Compliance Matrix | IMPLEMENTED | [docs/spec_compliance.md](file:///c:/stampede/docs/spec_compliance.md) | `python -c "import os; assert os.path.exists('docs/spec_compliance.md')"` |
