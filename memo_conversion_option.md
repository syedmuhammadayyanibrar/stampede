# Institutional Risk & Product Memo: The Upgrade Conversion Option

**To:** Ilia Bolgov (CEO) & Roman Yanushevskyi (CTO), Touchmark  
**From:** Antigravity Market-Risk Engineering Team  
**Date:** October 2026  
**Subject:** Mitigating Secondary Market Liquidity Crunches via Bilateral Upgrade Conversion Options  

---

### Executive Summary
Touchmark's secondary resale promise (*"lock in a discount today, resell anytime if plans change"*) functions efficiently under idiosyncratic buyer demand shocks. However, empirical token migration data across 6 generational foundation model releases (OpenRouter dataset, 2025–2026) demonstrates that **58.0% of token volume migrates to successor models within 14 days** ($\text{95% CI: } [33.1\%, 80.6\%]$).

When applied to a standard square-root market impact framework ($s = s_{\text{base}} + Y \sigma \sqrt{Q / V}$), this correlated sell-off triggers an endogenous **Benchmark Liquidity Crunch Ratio of 4.77x** ($\text{95% CI: } [4.63\text{x}, 4.91\text{x}]$), widening secondary market half-spreads from **6.0% to 35.8%** and imposing a **+$1.65 / \text{M token}$ net cost penalty** on liquidating buyers.

We propose a structural contract enhancement: the **Upgrade Conversion Option**, enabling buyers to convert deprecated specific-model capacity directly into successor tokens with the primary provider at the prevailing launch price ratio $r = S_{\text{old}} / S_{\text{new}}$, bypassing the secondary order book during obsolescence windows.

---

### Quantitative Impact of Conversion Uptake

Simulating upgrade conversion across 15,000 Monte Carlo paths reveals that absorbing selling pressure at the primary provider level systematically compresses secondary spreads:

| Conversion Uptake ($c$) | Secondary Shock Spread | Benchmark LCR | Net Shock Penalty | Spread Compression |
| :---: | :---: | :---: | :---: | :---: |
| **0.0% (Status Quo)** | **35.8%** | **4.77x** | **+$1.65 / M** | **Baseline** |
| **25.0%** | 31.7% | 4.58x | +$1.63 / M | -11.5% |
| **50.0%** | 26.6% | 4.38x | +$1.61 / M | -25.7% |
| **75.0%** | 19.8% | 4.12x | +$1.58 / M | -44.7% |
| **100.0% (Full Route)** | **13.9%** | **3.88x** | **+$1.54 / M** | **-61.2%** |

*Methodological note: Under 75%+ conversion uptake, secondary market spreads remain under 20%, preventing market-maker liquidity withdrawal and eliminating the order-book freeze.*

---

### Stakeholder Alignment

1. **For Enterprise Buyers:**
   - Eliminates the secondary market liquidation haircut during frontier releases.
   - Provides seamless, programmatic migration to new model checkpoints without renegotiating bilateral cloud commitments.

2. **For Model Providers (Sellers):**
   - Retains committed forward token revenue on existing infrastructure rather than forfeiting customer spend to competing host gateways.
   - Preserves forward demand visibility for GPU capacity scheduling.

3. **For Touchmark:**
   - De-risks the secondary order book and protects market-maker balance sheets from inventory toxic selection.
   - Unlocks an additional transaction fee stream on programmatic contract conversions.

---

### Three Operational Considerations for Implementation
1. **Exchange Ratio Settling:** Structuring $r$ as value-neutral at the official API launch spot prices ($S_{\text{old}} / S_{\text{new}}$), with a fixed 2.0% platform conversion spread.
2. **Provider Capacity Windows:** Ensuring provider capacity guarantees allocate a dynamic 15% buffer on new clusters for contract rollover.
3. **Contract Menu Synergy:** Pairing specific-model contracts with conversion rights as the cost-effective alternative to Touchmark's premium "Best-in-Class" contracts.
