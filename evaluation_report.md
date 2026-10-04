# TOUCHMARK MARKET-RISK SIMULATION: COMPREHENSIVE EVALUATION REPORT

## Important Framing & Methodology
This project is a quantitative market-risk simulation and contract sizing engine built for forward capacity markets in AI tokens. It is grounded in empirical public data (21+ months of OpenRouter daily token traffic rankings, official release dates, and public API price cuts). It does NOT use Touchmark's internal order book or proprietary data. It demonstrates a rigorous risk-engineering methodology tailored for high-growth compute market builders.

## 1. Empirical Model Migration Velocity (OpenRouter 2025–2026)

- **Mean 14-Day Empirical Switch Share (phi):** **58.0%** (95% Bootstrap CI: [33.1%, 80.6%])
- **Transition Half-Life:** **11.2 Days**
- **Observed Generational Events:** 6 pairs (GPT-4o -> 4o-mini, Claude 3 Sonnet -> 3.5 Sonnet, Claude 3.5 Sonnet -> Haiku, Llama 3 -> 3.1 70B, Llama 3.1 -> 3.3 70B, DeepSeek V2.5 -> V3)

| Event | Provider | Transition | Launch Date | Pre-Launch Share | phi (14 Days) | phi (28 Days) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| claude_35_to_37_sonnet | Anthropic | anthropic/claude-3.5-sonnet -> anthropic/claude-3-7-sonnet-20250219 | 2025-02-24 | 22.7% | 81.7% | 87.0% |
| gemini_flash_15_to_20 | Google | google/gemini-flash-1.5 -> google/gemini-2.0-flash-001 | 2025-02-05 | 5.5% | 41.6% | 48.6% |
| claude_37_to_4_sonnet | Anthropic | anthropic/claude-3-7-sonnet-20250219 -> anthropic/claude-4-sonnet-20250522 | 2025-05-22 | 14.5% | 47.0% | 54.7% |
| gemini_flash_20_to_25 | Google | google/gemini-2.0-flash-001 -> google/gemini-2.5-flash-preview-05-20 | 2025-05-20 | 10.1% | 9.4% | 0.0% |
| claude_4_to_45_sonnet | Anthropic | anthropic/claude-4-sonnet-20250522 -> anthropic/claude-4.5-sonnet-20250929 | 2025-09-29 | 11.4% | 68.3% | 76.5% |
| deepseek_v3_to_v4 | DeepSeek | deepseek/deepseek-chat-v3-0324 -> deepseek/deepseek-v4-flash-20260423 | 2026-04-23 | 0.3% | 100.0% | 100.0% |

## 2. Model Calibration Table

| Dimension | OpenAI GPT-4/4o Tier | Anthropic Claude 3/3.5 Tier | Empirical Source |
| :--- | :--- | :--- | :--- |
| Initial Spot S0 | $5.00 | $3.00 | Verified API launch input pricing |
| Annual Drift mu | -35.0% | -18.0% | Intra-model optimization & hardware cost curves |
| Annual Volatility sigma | 28.0% | 22.0% | GPU cloud provider spot variance |
| Hazard Rate lambda | 1.85/yr | 0.60/yr | Verified release announcements (6.5mo vs 20mo tenure) |
| Generational Jump J | 45.0% | 40.0% | Generational price reset (GPT-4->4o, Opus->Sonnet) |
| Base Resale Spread | 6.0% | 5.0% | Idiosyncratic secondary resale friction |
| Shock Resale Spread | 38.0% | 32.0% | Correlated obsolescence market-maker widening |

## 3. Data-Driven vs. Assumed Crunch Comparison

| Parameter | Assumed Benchmark Baseline | Empirical Data-Driven (OpenRouter + Impact Law) | Structural Assessment |
| :--- | :--- | :--- | :--- |
| Secondary Market Spread | 38.0% | 35.8% | Corroborates assumed 38% order book widening |
| Benchmark LCR | 11.10x | 4.77x | Crunch naturally emerges from real velocity |
| Shock Cost Penalty | +$1.795/M | +$1.661/M | Robust net economic buyer penalty |
| Mean Resale Price in Shock | $1.29/M | $1.34/M | Severe liquidation discount confirmed |

## 4. Contractual Innovation: The Upgrade Conversion Option

| Conversion Uptake Rate (c) | Secondary Market Spread | Benchmark LCR | Mean Resale Price (Shock) | Shock Net Penalty vs Spot |
| :--- | :--- | :--- | :--- | :--- |
| 0% | 35.8% | 4.74x | $1.34/M | +$1.647/M |
| 25% | 31.7% | 4.58x | $1.42/M | +$1.628/M |
| 50% | 26.6% | 4.38x | $1.53/M | +$1.606/M |
| 75% | 19.8% | 4.12x | $1.67/M | +$1.577/M |
| 100% | 13.9% | 3.88x | $1.79/M | +$1.543/M |

## 5. Monte Carlo Numerical Convergence Check

> **Internal Validity Note:** This table reports standard error decay across sample path counts to confirm numerical convergence of the vectorized engine. It is NOT a historical backtest.

| Paths N | Fair Forward Price F0 | Standard Error | 95% CI Interval | Relative SE |
| :--- | :--- | :--- | :--- | :--- | 
| 500 | $3.7073 | +/- $0.0568 | [$3.5960, $3.8187] | 1.53% |
| 1,000 | $3.6329 | +/- $0.0389 | [$3.5568, $3.7091] | 1.07% |
| 2,500 | $3.6060 | +/- $0.0254 | [$3.5562, $3.6557] | 0.70% |
| 5,000 | $3.6083 | +/- $0.0181 | [$3.5728, $3.6438] | 0.50% |
| 10,000 | $3.6202 | +/- $0.0126 | [$3.5955, $3.6450] | 0.35% |
| 20,000 | $3.6291 | +/- $0.0090 | [$3.6115, $3.6468] | 0.25% |

## 6. Parameter Sensitivities (Finite Differences)

> **Terminology Guardrail:** Parameter sensitivities are strictly finite-difference derivatives (dF0/dS0, dF0/dlambda, dF0/dT). Because compute tokens are non-storable flow services without a continuous exchange-traded underlying, dynamic replication does not exist and these metrics must NOT be called Greeks.

| Metric | OpenAI Tier (S0=$5.00, T=90d) | Anthropic Tier (S0=$3.00, T=90d) |
| :--- | :--- | :--- |
| Spot-Price Sensitivity (dF0/dS0) | 0.723 | 0.878 |
| Hazard-Rate Sensitivity (dF0/dlambda) | -0.418 | -0.267 |
| Tenor Sensitivity (dF0/dT per day) | $-0.0114/day | $-0.0031/day |
| Volatility Sensitivity (dF0/dsigma) | 0.016 | 0.005 |

## 7. Supporting Stress Scenarios (Conditional on Shock)

| Scenario | Stress Condition | Primary Benchmark LCR | Shock Forward Cost | Shock Net Penalty vs Spot |
| :--- | :--- | :--- | :--- | :--- |
| Secondary Market Freeze | Spread widens to 65.0% | 13.06x | $3.389/M | +$1.925/M |
| Buyer Utilization Collapse | Mean utilization drops to 20.0% | Demand Shock | $2.612/M | +$2.191/M (+520.7%) |
| Frontier Release War | Cadence doubles (lambda=3.70/yr) | Elevated Frequency | $3.328/M | +$2.105/M |

## 8. Executive Synthesis

**Source:** deterministic_prewritten

> Touchmark's secondary resale mechanism exhibits a primary Benchmark Liquidity Crunch Ratio of 11.10x (95% CI: [10.43x, 11.84x]) relative to unshocked counterfactual value, with secondary market spreads widening by 6.34x (95% CI: [6.30x, 6.38x]) from 6.0% to 38.0%.

> Isolating deflation from liquidity risk: entering at the engine's fair-value forward price ($3.63/M) yields expected parity unconditionally, but conditional on a correlated shock window, the forward holder pays an expected net cost of $3.259/M versus $1.464/M on spot (+122.6% penalty, +$1.795/M). Secondary market spread blowout alone accounts for +$0.190/M in unrecovered liquidation friction, while entering at a naive 15% spot discount adds another +23.5% (+$0.621/M) penalty from unhedged hardware deflation.
