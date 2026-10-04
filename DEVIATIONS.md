# Parity Architectural & Implementation Deviations

This document logs all explicit deviations, structural design choices, and remediation actions taken across the Stampede repository and the Parity extension.

---

## DEV-001: Legacy Web UI Uncomputed Metrics & Strict No-UI Boundary
- **Context:** The project specification establishes an absolute rule:
  > *NO UI. Do not create, modify or delete anything under web/. Write no HTML, CSS or JS, no plotting code, no matplotlib, no images. Every output is JSON, markdown or a terminal table (rich).*
- **Observation:** `web/index.html` contains several uncomputed or inconsistent static literals inherited from earlier iterations:
  - Line 335: Uncomputed "11.2 Days" half-life claim.
  - Lines 466 & 472: Hardcoded `+$1.67 / M` and `$1.81 / M` in the comparison table, differing slightly from the freshly computed `$1.65 / M` and `$1.88 / M`.
- **Decision:** In strict compliance with the NO UI rule, no files under `web/` were modified. The discrepancies are acknowledged and recorded here. All authoritative quantitative results are produced in JSON artifacts, markdown reports, and terminal rich outputs.

---

## DEV-002: v1 Remediation & Empirical Integrity
- **Context:** An audit of the Stampede v1 codebase revealed several ungrounded claims, stale event lists, and evaluation discrepancies.
- **Actions Taken:**
  1. **Uncomputed Transition Half-Life:** Removed the uncomputed "11.2 Days" metric from `README.md`, `evaluation_report.md`, and `cli_report.py`.
  2. **Generational Event Alignment:** Corrected the prose listing of 6 generational transitions in `README.md`, `evaluation_report.md`, and `cli_report.py` to match the actual verified historical records in `data/launch_events.json`:
     - Claude 3.5 Sonnet -> Claude 3.7 Sonnet
     - Gemini Flash 1.5 -> Gemini Flash 2.0
     - Claude 3.7 Sonnet -> Claude 4 Sonnet
     - Gemini Flash 2.0 -> Gemini Flash 2.5 Preview
     - Claude 4 Sonnet -> Claude 4.5 Sonnet
     - DeepSeek V3 -> DeepSeek V4 Flash
  3. **Spread Compression Clarification:** Explicitly qualified the "61.2%" metric in `README.md` as secondary market spread compression (from 35.8% to 13.9% under 100% conversion uptake) rather than an overall customer cost reduction.
  4. **Keyword Heuristic Labeling:** Explicitly labeled `copilot/fit_check.py` in documentation as a keyword-matching heuristic that is superseded by Parity's Bayesian non-inferiority engine.
  5. **Dynamic Threshold Loading & Diagnostic Sizing:** Refactored `run_evals.py` to load evaluation gates directly from `evals/thresholds.yaml` (enforcing the pre-committed 0.80 recall threshold) rather than relying on loose hardcoded literals. Added the forecast-mean sizing baseline as an honest diagnostic row (+0.01%) alongside the passing P90 newsvendor sizing gate (+4.45%).

---

## DEV-003: G04 Clear-Cell Holdout Difference Wilson Calibration
- **Context:** Sequential posteriors from probe prompts must be calibrated against holdout observations without leaking data or overfitting boundary noise.
- **Decision:** As pre-committed in Section 1.1 of the design specification, the evaluation compares sequential posteriors against the holdout rate $\theta_{hold}$ using difference Wilson intervals at 80% confidence. This isolates clear non-inferior ($\Delta \ge -0.05$) and clear inferior cells, yielding a holdout Brier calibration score of 0.0411 (well below the 0.15 ceiling).

---

## DEV-004: G11 Provider-Specific Deprecation Velocity
- **Context:** Cross-sectional depreciation velocity ranking requires discriminative model degradation models across market participants.
- **Decision:** Calibrated provider-specific hazard and jump rates for OpenAI, Anthropic, Google, DeepSeek, Meta, and Mistral across verified release history. This achieved a walk-forward Spearman rank correlation of $\rho = 0.9189$ (exceeding the 0.70 threshold).

---

## DEV-005: G20 Uniform Marginal Price Double Auction
- **Context:** G20 requires an auction envy-freeness rate $\ge 0.95$ alongside market welfare uplift $\ge 1.08$.
- **Decision:** Bilateral mid-pricing created idiosyncratic execution prices across matched pairs, causing price dispersion that triggered buyer envy. Replacing bilateral execution prices with a uniform marginal clearing price $P^*$ for all cleared trades eliminates price dispersion, achieving an envy-freeness rate of 1.0 (100%) while preserving full matching welfare uplift (welfare ratio = 4.0064).

---

## DEV-006: G26 Sliced Capacity Allocation with Hard Provider Cap
- **Context:** Enterprise buyer portfolios require that no single provider exceeds 50% of the total allocated capacity when multi-provider diversification is requested.
- **Decision:** Greedy whole-ticket allocations with coarse requirement blocks can lead to single-provider concentration overruns. Implemented slice-based capacity allocation where individual requirements are bounded by each provider's remaining capacity ceiling and remainder volume is routed to the next non-inferior substitute. This guarantees strict compliance (max provider share = 47.83% $\le 50.0\%$).

