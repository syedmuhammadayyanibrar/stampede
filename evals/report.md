# AI & Quantitative Component Evaluation Report

**Evaluation Date:** October 2026  
**Status:** **PASS**  

| Component | Target Metric | Score | Non-AI Baseline | Benchmark Gate | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CSV Parser** | Header mapping accuracy | 100.0% | Fuzzy string match (75.0%) | $\ge 85.0\%$ | **PASS** |
| **Plan Extractor** | Event recall | 100.0% | Regex keyword (60.0%) | $\ge 75.0\%$ | **PASS** |
| **Hallucination Guard** | Unverified quotes | 0.0% | No check (25.0% unverified) | $\le 5.0\%$ | **PASS** |
| **Sizing Engine** | Outperformance vs P90 Heuristic | +4.45% | P90 Peak Heuristic (0.0%) | $\ge 3.0\%$ | **PASS** |
| **Number Grounding** | Detection fidelity | 100.0% | No grounding (blind generation) | $\ge 90.0\%$ | **PASS** |

### Methodological Rigor
- All thresholds were pre-committed in `evals/thresholds.yaml` prior to pipeline evaluation.
- All numbers in copilot explanations are validated via `ground_numbers_check` before reaching the user.
