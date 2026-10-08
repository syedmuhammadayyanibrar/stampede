# Stampede Live Mathematical Framework

This document details the quantitative models, stochastic differential equations, optimization objectives, and attribution formulations implemented in the Stampede engine.

---

## 1. Spot Price Jump-Diffusion & Deflation Process

Inference capacity spot prices $S_t$ evolve under continuous software/hardware efficiency improvements and discrete generational obsolescence events:

$$d\ln S_t = \left(\mu - \frac{1}{2}\sigma^2\right)dt + \sigma dW_t + \ln(1 - J) dN_t$$

Where:
- $\mu < 0$: Continuous hardware cost deflation rate (annualized).
- $\sigma$: GPU cloud cluster capacity utilization and spot volatility.
- $W_t$: Standard Brownian motion.
- $N_t$: Poisson jump process with hazard rate $\lambda$ representing arrival of superseding frontier models.
- $J \in (0, 1)$: Generational price collapse percentage upon release of superior architectures.

---

## 2. Sequential Bayesian Non-Inferiority Testing

To determine whether candidate model $A$ can substitute for incumbent model $B$ on enterprise prompt distribution $D$, task success outcomes $X_i \sim \text{Bernoulli}(p)$ are evaluated sequentially:

$$p_A \sim \text{Beta}(\alpha_0 + k, \beta_0 + n - k)$$

Where $\alpha_0 = 1, \beta_0 = 1$ is an uninformative uniform prior.

Non-inferiority is declared if the posterior probability that performance meets or exceeds margin $\delta$ satisfies:

$$\mathbb{P}(p_A \ge p_B - \delta \mid \mathcal{D}) \ge 1 - \alpha$$

### Bayesian Judge Operating Characteristic Adjustment
When evaluations are conducted by an LLM-as-a-judge with known sensitivity $Se$ and specificity $Sp$, raw positive classification rate $\hat{y}$ is adjusted via the Youden Index $J = Se + Sp - 1$:

$$p_{\text{adj}} = \frac{\hat{y} + Sp - 1}{Se + Sp - 1} = \frac{\hat{y} - (1 - Sp)}{J}$$

If Youden index $J \le 0.20$, the judge is rejected as uninformative, and the pipeline halts or falls back to ground-truth deterministic verifiers.

### Effective Cost Per Acceptable Task ($C^*$)
The effective economic cost per successful task accounts for candidate failure rate $q = 1 - p$:

$$C^* = \frac{c_{\text{in}} T_{\text{in}} + c_{\text{out}} T_{\text{out}}}{1 - q}$$

---

## 3. American Resale Option Valuation (Longstaff-Schwartz)

Unused forward capacity can be liquidated on the secondary market at any exercise time $t \in \{t_1, \dots, t_K\}$. The optimal stopping problem is solved via least-squares Monte Carlo (LSM):

$$V_0 = \sup_{\tau \in \mathcal{T}} \mathbb{E}^\mathbb{Q} \left[ e^{-r\tau} (S_\tau(1 - s_\tau) - F_0)^+ \right]$$

At each intermediate exercise date $t_k$, the continuation value $C(S_{t_k})$ is approximated by projecting discounted future cash flows onto a polynomial basis of spot price states:

$$\hat{C}(S_{t_k}) = \sum_{m=0}^2 \beta_m S_{t_k}^m$$

Early exercise occurs when immediate exercise payoff exceeds estimated continuation value:

$$\text{Payoff}(S_{t_k}) > \hat{C}(S_{t_k})$$

---

## 4. Exact 5-Factor Shapley Risk Decomposition

The forward contract risk discount is decomposed into 5 orthogonal economic drivers across all $2^5 = 32$ characteristic subsets:

$$\phi_i(v) = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!(|N| - |S| - 1)!}{|N|!} \left[ v(S \cup \{i\}) - v(S) \right]$$

The five decomposed factors are:
1. **Price-Cut Dynamics & Deflation ($\mu$):** Expected depreciation of compute costs.
2. **Demand Uncertainty & Plan Shifts ($\sigma_{\text{demand}}$):** Volatility in token consumption.
3. **Shutdown & Obsolescence Hazard ($\lambda, J$):** Risk of immediate generational deprecation.
4. **Resale Liquidation Option ($V_{\text{resale}}$):** Capital recovery benefit through secondary trading.
5. **Financing Drag & Risk Aversion ($r, \gamma$):** Cost of capital lockup and downside risk buffer.

Efficiency is verified numerically to machine precision: $\left|\sum_{i=1}^5 \phi_i - v(N)\right| < 10^{-9}$.

---

## 5. Capacity Sizing ($Q^*$) Under Asymmetric Liquidation Salvage

Token consumption follows a log-drift geometric Brownian process with baseline drift $\hat\mu_d$, empirical volatility $\hat\sigma_d$, and milestone plan multipliers $M_t$:

$$D_T = D_0 \exp\left( (\hat\mu_d - 0.5\hat\sigma_d^2)T + \hat\sigma_d W_T \right) \cdot \prod_{j} M_j$$

Optimal forward procurement volume $Q^*$ solves the generalized Newsvendor objective:

$$\min_Q \mathbb{E} \left[ C_u (D_T - Q)^+ + C_o (Q - D_T)^+ \right]$$

Where:
- Underage unit cost: $C_u = S_0 - F_0$ (cost penalty of paying spot for demand above commitment).
- Overage unit cost: $C_o = F_0 - R_T = F_0 - S_0(1 - s_{\text{sec}})$ (net loss per unutilized token salvaged at secondary price $R_T$).

The optimal commitment tranche corresponds to the critical ratio:

$$Q^* = F_D^{-1} \left( \frac{C_u}{C_u + C_o} \right)$$

---

## 6. Microstructural Liquidity & Market Impact Law

Secondary market illiquidity widens bid-ask spreads during correlated liquidation events according to the square-root market impact law:

$$s = s_{\text{base}} + \kappa \left( \frac{\Delta V}{V_{\text{daily}}} \right)^\alpha$$

With $\alpha = 0.5$ (canonical square-root law).

When a superseding frontier model is released, correlated switch share $\hat\phi$ drives liquidation volume $\Delta V = \hat\phi \cdot Q_{\text{total}}$, inflating secondary spreads and depressing net capital recovery:

$$R_{\text{shock}} = S_{\text{post-jump}} \cdot \left(1 - s_{\text{shock}}\right)$$

### Upgrade Conversion Option Compression
Under a contractual par-value upgrade conversion option, a fraction $\gamma_{\text{conv}}$ of obsolete capacity is absorbed directly into replacement model allocations, eliminating market dump volume:

$$\Delta V_{\text{net}} = \Delta V \cdot (1 - \gamma_{\text{conv}})$$

Compressing secondary spread widening by up to 61.2% at full conversion adoption.
