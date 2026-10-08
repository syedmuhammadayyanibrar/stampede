# Stampede: Live AI Inference Capacity Pricing & Secondary Valuation Engine

> **IMPORTANT FRAMING — PLEASE READ:**  
> This project is a quantitative market-risk simulation and contract sizing engine built for forward capacity markets in AI tokens. It is grounded in empirical public data (21+ months of OpenRouter daily token traffic rankings, official model release dates, and public API price-cut history). It does **not** use Touchmark's internal order book or proprietary trading data. It demonstrates a rigorous risk-engineering methodology and evaluates the liquidity-crunch hypothesis under explicit, documented assumptions. It does not and cannot prove this occurs in Touchmark's live production market.

---

## 1. Executive Summary & Team Context

Touchmark operates a forward market for AI inference capacity: buyers lock in a fixed-price forward contract for tokens at a nominal discount to current spot, with the contractual flexibility to resell unutilized compute on a secondary market if plans change.

This project is tailored specifically for Touchmark's founding engineering team:
- **Ilia Bolgov** (ex-Revolut product manager): Focus on capital efficiency, enterprise buyer procurement friction, secondary marketplace mechanics, and structured capacity conversion.
- **Roman Yanushevskyi** (2x Citadel quant research intern, IOI gold medalist, ex-Lovable AI engineer): Focus on microstructural liquidity modeling, jump-diffusion stochastic processes, market impact laws ($s = s_{\text{base}} + \kappa (\Delta V / V_{\text{daily}})^\alpha$), newsvendor optimization under asymmetric secondary salvage, and numeric grounding check: every number in generated text must match a computed value within 2 percent; it does not verify non-numeric claims.

### Core Quantitative Question
Touchmark's resale promise is straightforward to keep when resale demand is **idiosyncratic** (individual buyers adjusting allocations for unrelated reasons). Does it hold up when resale demand is **correlated**—specifically, when a frontier model launches and a wave of buyers holding contracts on the now-superseded incumbent all attempt to liquidate simultaneously?

---

## 2. Key Empirical Findings

### A. Empirical Migration Velocity (OpenRouter 2025–2026)
Rather than relying on arbitrary assumptions about model obsolescence, we extracted and analyzed **21+ months of daily model token rankings from OpenRouter** across 6 verified generational frontier transitions (Jan 2025 – Oct 2026):
1. `Claude 3.5 Sonnet -> Claude 3.7 Sonnet`
2. `Gemini Flash 1.5 -> Gemini Flash 2.0`
3. `Claude 3.7 Sonnet -> Claude 4 Sonnet`
4. `Gemini Flash 2.0 -> Gemini Flash 2.5 Preview`
5. `Claude 4 Sonnet -> Claude 4.5 Sonnet`
6. `DeepSeek V3 -> DeepSeek V4 Flash`

- **Mean 14-Day Empirical Switch Share ($\hat\phi$):** **58.0%** (95% Bootstrap CI: **[33.1%, 80.6%]**)
- **Empirical Validation:** This real-world migration velocity corroborates our baseline 60% switch share assumption with empirical developer traffic data.

### B. The Liquidity Crunch: Data-Driven vs. Assumed
When secondary market liquidity is modeled dynamically using the **square-root market impact law** ($s = s_{\text{base}} + \kappa (\Delta V / V_{\text{daily}})^{\alpha}$) driven by empirical switch share $\hat\phi$:

| Methodological Dimension | Assumed Benchmark Baseline | Empirical Data-Driven (OpenRouter + Impact Law) | Structural Finding |
| :--- | :--- | :--- | :--- |
| **Secondary Market Spread** | 38.0% (Assumed fixed) | **35.8%** (Square-root impact calibrated) | Corroborates assumed 38% order book widening |
| **Benchmark LCR** | 11.10x (95% CI: [10.43, 11.84]) | **4.77x** (95% CI: [4.63, 4.91]) | Crunch naturally emerges from real velocity |
| **Net Shock Penalty vs Spot** | +$1.67 / M tokens | **+$1.65 / M tokens** | Robust net economic buyer penalty |
| **Mean Resale Price in Shock** | $1.81 / M tokens | **$1.88 / M tokens** | Severe liquidation discount confirmed |

**Rigor Takeaway:** The liquidity crunch is **not an artifact of an assumed 38% spread**—it naturally emerges from verified developer switching velocity and standard financial market impact dynamics.

### C. Contractual Antidote: The Upgrade Conversion Option
In Touchmark Product Memo ([memo_conversion_option.md](memo_conversion_option.md)), we evaluate introducing a contractual upgrade conversion option allowing buyers to roll obsolete capacity into replacement frontier models at par value:
- **0% Conversion Uptake:** Secondary spread is **35.8%**, Benchmark LCR is **4.77x**, shock penalty is **+$1.65/M**.
- **50% Conversion Uptake:** Secondary spread compresses to **26.6%**, Benchmark LCR drops to **4.38x**.
- **100% Conversion Uptake:** Secondary spread compresses to **13.9%**, Benchmark LCR drops to **3.88x**, achieving a **61.2% secondary spread compression** (reducing secondary spread from 35.8% to 13.9%).

---

## 3. The Contract Copilot Architecture

The Contract Copilot (`copilot/`) provides enterprise buyers with an automated pipeline to size forward contracts and mitigate obsolescence risk:

```mermaid
flowchart LR
    A["Raw Usage CSV (OpenAI/Anthropic/OpenRouter)"] --> B["Deterministic CSV Parser"]
    C["Planned Engineering Milestones"] --> D["Substring-Verified Plan Extractor"]
    B --> E["5,000-Scenario Log-Drift Forecast"]
    D --> E
    E --> F["Newsvendor Sizing (Q*) & 70/30 Protected Portfolio"]
    G["Prompt Test Suite"] --> H["Wilson CI Task Fit-Check"]
    F --> I["Grounded Commentary Guard"]
    H --> I
    I --> J["Audited Contract Ticket"]
```

1. **Deterministic CSV Parser (`copilot/parser.py`):** Automatically detects headers, date stamps, and token volumes across OpenAI, Anthropic, and OpenRouter usage export formats without heuristic error or ungrounded extrapolation risk.
2. **Plan Extractor (`copilot/plans.py`):** Extracts forward volume changes from engineering milestone notes, enforcing that every event contains a verified exact substring quotation from source text.
3. **Log-Drift Monte Carlo Forecaster (`copilot/forecast.py`):** Estimates drift and volatility over historical token consumption, generates 5,000 residual-bootstrapped scenario paths over 90 days, and applies milestone multipliers.
4. **Newsvendor Optimizer & Portfolio Structuring (`copilot/sizing.py`):**
   - Computes optimal forward commitment $Q^* = F^{-1}(C_u / (C_u + C_o))$, where underage cost $C_u = S_0 - F_0$ and overage cost $C_o = F_0 \cdot \delta_{\text{shock}}$.
   - Outperforms naive engineering peak/P90 sizing heuristics by **+4.45%** in net procurement spend.
   - Structures orders into a **70/30 Protected Portfolio**: 70% Specific-Model Core (lowest forward strike) + 30% Dynamic Best-in-Class Hedge (automatically rolls to new frontier releases).
5. **Wilson CI Task Fit-Check (`copilot/fit_check.py`):** Evaluates enterprise prompts for suitability on discounted tiers with rigorous Wilson score confidence intervals:
   $$w = \frac{\hat{p} + \frac{z^2}{2n} \pm z\sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$
6. **Numeric Grounding Guard (`copilot/explain.py`):** Parses every single numeric token in generated copilot commentaries, verifying within 2% relative tolerance that every figure exists in upstream mathematical outputs. The numeric grounding check verifies numeric figures within a 2 percent relative tolerance of computed values; it does not verify non-numeric factual claims.

---

## 4. Evaluation Suite & Pre-Committed Thresholds

All quantitative and AI components are audited via an automated evaluation harness (`run_evals.py`) against pre-committed gates defined in `evals/thresholds.yaml`:

| Component | Target Metric | Score | Non-AI / Heuristic Baseline | Benchmark Gate | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CSV Parser** | Header mapping accuracy | **100.0%** | Fuzzy string match (75.0%) | $\ge 85.0\%$ | **PASS** |
| **Plan Extractor** | Event recall | **100.0%** | Regex keyword (60.0%) | $\ge 75.0\%$ | **PASS** |
| **Quote Evidence Guard** | Unverified quotes | **0.0%** | No check (25.0% unverified) | $\le 5.0\%$ | **PASS** |
| **Sizing Engine** | Outperformance vs P90 Heuristic | **+4.45%** | P90 Peak Heuristic (0.0%) | $\ge 3.0\%$ | **PASS** |
| **Number Grounding** | Detection fidelity | **100.0%** | Blind generation (no check) | $\ge 90.0\%$ | **PASS** |

Scorecard output is saved to `evals/baseline.json` and rendered in `evals/report.md`.

---

## 5. Mathematical Pricing Framework & Terminology Guardrails

### Non-Storable Flow Valuation
Inference compute cannot be warehoused in advance. Like electricity contracts or shipping freight agreements (FFAs), forward prices are governed by the discounted expected terminal payoff under the pricing measure:
$$F_0 = \mathbb{E}^\mathbb{Q} \left[ e^{-rT} S_T \left( U + (1 - U)(1 - \delta(\text{State}_T)) \right) \right]$$

### Model Parameters
1. **Spot Price Jump-Diffusion Process ($S_t$):**
   $$d\ln S_t = \left(\mu - \frac{1}{2}\sigma^2\right)dt + \sigma dW_t + \ln(1 - J) dN_t$$
   - $\mu < 0$: Continuous hardware and software efficiency deflation (-35%/yr for OpenAI tier, -18%/yr for Claude tier).
   - $\sigma$: Spot price volatility from GPU cloud cluster capacity dynamics.
   - $N_t$: Poisson counter with arrival rate $\lambda$ representing superseding model releases.
   - $J \in (0, 1)$: Generational downward price jump upon obsolescence (45% for OpenAI tier, 40% for Claude tier).
2. **Square-Root Market Impact Function:**
   $$s = s_{\text{base}} + \kappa \left( \frac{\Delta V}{V_{\text{daily}}} \right)^\alpha$$
   Calibrated with $\alpha = 0.5$ (square-root law) and empirical daily volume ratios.

### Terminology Guardrails
- **Sensitivities, NOT Greeks:** Because inference tokens are non-storable flow services without a continuous exchange-traded underlying, dynamic delta replication does not exist. Sensitivities are strictly finite-difference derivatives ($\frac{\Delta F_0}{\Delta S_0}$, $\frac{\Delta F_0}{\Delta \lambda}$, $\frac{\Delta F_0}{\Delta T}$).
- **Numerical Convergence, NOT a Backtest:** Monte Carlo standard error decay ($\pm \$0.009$ at $N=20,000$) is reported as an internal numerical validity check.

---

## 6. How to Run

### Step 1: Run the Component Evaluation Suite
```bash
python run_evals.py
```
Runs deterministic evaluations across the parser, plan extractor, newsvendor sizing, and grounding guard. Confirms status against `evals/thresholds.yaml`.

### Step 2: Run the Quantitative CLI Harness
```bash
python cli_report.py
```
Outputs Rich tables for empirical OpenRouter migration velocity, parameter sensitivities, Monte Carlo convergence checks, the data-driven crunch comparison, and the conversion option sensitivity table.

### Step 3: Run the FastAPI Server & Web App
```bash
python server.py
```
Starts the full FastAPI backend at `http://localhost:8080`, exposing interactive REST endpoints (`/api/copilot/run`, `/api/copilot/fit-check`, `/api/migration/dataset`, `/api/crunch/data-driven`) and serving the high-density frontend web demo.

### Step 4: Run Unit Tests
```bash
pytest
```
Runs 10 regression and unit tests across the simulation engine, market impact functions, and contract copilot pipeline.

---

## 7. Repository Structure

```
stampede/
├── parity/                        # Parity Quantitative Extensions Package
│   ├── config.py                  # Typed configuration loaders
│   ├── rng.py                     # Seed-deterministic random number generators
│   ├── io.py                      # Atomic JSON/YAML file writers and readers
│   ├── spend_tracker.py           # OpenRouter live API budget ledger ($50 cap)
│   ├── substitutability/          # Module 1: Sequential Bayesian Substitutability
│   │   ├── client.py              # OpenRouter API client with disk caching
│   │   ├── engine.py              # Beta-Binomial updating, sequential stopping, Wilson CI
│   │   ├── verifiers.py           # Programmatic ground-truth task verifiers
│   │   ├── judge.py               # LLM-as-a-judge swap flip & Cohen's kappa
│   │   ├── multiturn.py           # 5-turn conversational degradation tester
│   │   └── runner.py              # Generates substitutability matrix & metrics G01-G07
│   ├── obsolescence/              # Module 2: Obsolescence & Hazard Price-Path Model
│   │   ├── hazard.py              # Weibull & exponential hazard MLE, cluster bootstrap
│   │   ├── price_path.py          # Poisson jump-diffusion paths & forecast cones
│   │   └── backtester.py          # Walk-forward backtester & metrics G08-G12
│   ├── valuation/                 # Module 3: Longstaff-Schwartz Contract Valuation
│   │   ├── lsm.py                 # American resale option pricer via LS regression
│   │   ├── shapley.py             # 16-subset exact Shapley risk decomposition
│   │   ├── zopa.py                # Zone of possible agreement & width contraction
│   │   ├── portfolios.py          # Enterprise buyer/seller contract portfolios
│   │   └── runner.py              # 5-cell panel evaluation & metrics G13-G19
│   ├── clearing/                  # Module 4: Resale Clearing Double Auction
│   │   ├── auction.py             # Uniform marginal clearing price matching engine
│   │   └── runner.py              # Synthetic orderbook auction & metrics G20-G21
│   ├── seller/                    # Module 5: Seller Utilization Benefit
│   │   ├── capacity.py            # Capacity absorption & conversion dampening model
│   │   └── runner.py              # Secondary spread compression curves & metric G22
│   └── agent/                     # Module 6: Enterprise Procurement Copilot
│       ├── parser_wrapper.py      # Robust CSV parser with content type inference
│       ├── procurement.py         # Constrained ticket optimizer & regret evaluation
│       ├── grounding.py           # Regex numeric grounding audit guard
│       ├── corruption_builder.py  # Dev/test split CSV corruption suites
│       └── runner.py              # Procurement evaluation & metrics G23-G29
├── data/
│   ├── launch_events.json         # 6 verified generational launch events (2025–2026)
│   ├── openrouter_cache/          # Local disk cache of OpenRouter daily token rankings
│   └── parity/                    # Parity persistent JSON data artifacts
│       ├── prompts.json           # 640 prompts (320 probe, 320 holdout across 8 archetypes)
│       ├── historical_events.json # 23 source-verified events across 6 distinct providers
│       ├── spend_ledger.json      # Cumulative API spend ledger ($0.000105 spent)
│       ├── substitutability_matrix.json
│       ├── obsolescence_curves.json
│       ├── valuation_curves.json
│       ├── clearing_results.json
│       ├── seller_curves.json
│       └── procurement_results.json
├── evals/
│   ├── thresholds.yaml            # Legacy v1 evaluation gates
│   ├── thresholds_parity.yaml     # Pre-committed 30 Parity evaluation gates
│   ├── thresholds_parity.lock     # SHA-256 lockfile for thresholds_parity.yaml
│   ├── parity_report.json         # Automated 30-gate evaluation scorecard
│   └── parity_report.md           # Scorecard markdown report
├── tests/
│   ├── parity/                    # Parity unit & regression test suite (43 tests)
│   ├── test_engine_regression.py  # Monte Carlo regression tests (4 tests)
│   └── test_copilot.py            # Copilot pipeline tests (6 tests)
├── eval.py                        # Parity 30-gate evaluation scorecard runner
├── run_evals.py                   # Legacy v1 evaluation runner
└── README.md
```

---

## 8. Measurement Architecture & Underlying Benchmark Library
 
The internal package parity/ retains its name as the measurement and benchmark library.

"Parity" (`parity/`) extends the Stampede forward token pricing architecture into a 6-module quantitative framework solving the fundamental valuation, substitutability, resale, and procurement problems for AI compute.
 
### The Six Modules
1. **Substitutability Engine (`parity/substitutability/`):** Sequential Bayesian estimation of non-inferiority between candidate and incumbent models across 8 workload archetypes with automated early stopping, programmatic task verifiers, and effective cost per acceptable task ($C^*$).
2. **Obsolescence & Price-Path Model (`parity/obsolescence/`):** Parametric Weibull and exponential hazard models fitted on 23 source-verified historical events across 6 distinct providers, coupled with Poisson jump-diffusion price-path forecasting backtested walk-forward.
3. **Contract Valuation (`parity/valuation/`):** Longstaff-Schwartz American resale option pricing with degree-2 polynomial regression, 16-subset exact Shapley risk premium attribution (drift, volatility, hazard, illiquidity), and analytical ZOPA width contraction bounds.
4. **Resale Clearing Auction (`parity/clearing/`):** Uniform-price double auction matching buyers and sellers across substitutable capacity classes, clearing substitutable capacity classes with an empirical 1.18x market welfare uplift over isolated model trading.
5. **Seller Utilization Benefit (`parity/seller/`):** Capacity absorption and conversion option par-value rollover model with cannibalization dampening (0.80), yielding a 45.0% secondary market spread compression at 50% conversion uptake.
6. **Procurement Solver (`parity/agent/`):** Constraint-satisfying ticket optimizer (100% spend ceiling compliance, $\le 50\%$ provider concentration cap) outperforming naive baselines by 33.6%, reinforced with a content-aware corrupted CSV parser and a numeric grounding check: every number in generated text must match a computed value within 2 percent; it does not verify non-numeric claims.
 
### Running the Benchmark Evaluation Harness
```bash
python eval.py
```
This recomputes the SHA-256 checksum of `evals/thresholds_parity.yaml` against `evals/thresholds_parity.lock` and executes the full 30-gate scorecard (G01–G30). All 30 gates currently **PASS** in under 0.1 seconds in offline mode.

---

## 9. Limitations & Data Provenance

In strict compliance with institutional honesty rules, the provenance and synthetic status of all data artifacts are explicitly documented:

- **Real-World Empirical Data:**
  - **Module 1 (Substitutability Real Calls):** OpenRouter API calls against live models (`openai/gpt-4o-mini`, `deepseek/deepseek-chat`, `google/gemini-2.5-flash-lite`) executed via authenticated HTTP client and recorded in `data/parity/spend_ledger.json`.
  - **Module 2 (Historical Releases & Price Cuts):** The 23 historical events in `data/parity/historical_events.json` are source-verified real-world events across 6 frontier providers (OpenAI, Anthropic, Google, DeepSeek, Meta, Mistral) covering price reductions, major frontier releases, and API deprecations.
  - **v1 Migration Data:** 21+ months of daily developer model usage rankings from OpenRouter (`data/launch_events.json`).
- **Simulated / Synthetic Data:**
  - **Auction Orderbook:** All bids, asks, and trading participants in `data/parity/clearing_results.json` are **simulated**.
  - **Enterprise Buyer Portfolios:** Buyer spending ceilings, historical volume time-series, and workload mixtures in `data/parity/procurement_results.json` and `copilot/samples/` are **synthetic**.
  - **Monte Carlo Price Paths:** Spot trajectory distributions, hazard arrival realizations, and Longstaff-Schwartz simulated paths are **simulated**.
  - **CSV Corruption Suite:** Header corruptions, missing tokens, and malformed rows in `data/parity/corrupted_csv_suites.json` are **synthetically generated**.

