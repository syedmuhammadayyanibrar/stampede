import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
from models import ModelCalibration, CALIBRATED_MODELS, MarketScenario, LiquidityCalibration
from engine import run_monte_carlo, SimulationResult

@dataclass
class CrunchExperimentResult:
    calibration: ModelCalibration
    tenor_days: int
    num_paths: int
    initial_spot: float
    advertised_discount_pct: float
    strike_price_naive: float
    fair_forward_price: float
    num_shock_paths: int
    num_normal_paths: int
    shock_prob_empirical: float
    mean_spot_normal: float
    mean_spot_shock: float
    mean_resale_normal: float
    mean_resale_shock: float
    resale_spread_normal: float
    resale_spread_shock: float
    lcr_benchmark: float
    lcr_benchmark_ci_lower: float
    lcr_benchmark_ci_upper: float
    lcr_spread: float
    lcr_spread_ci_lower: float
    lcr_spread_ci_upper: float
    fair_cost_spot_shock: float
    fair_cost_fwd_no_liq_shock: float
    fair_cost_fwd_actual_shock: float
    fair_total_shock_penalty: float
    fair_total_shock_penalty_pct: float
    fair_liquidity_blowout_penalty: float
    naive_expected_net_cost_forward: float
    naive_expected_cost_ondemand: float
    naive_net_cost_penalty: float
    naive_net_cost_penalty_pct: float
    stress_scenarios: Dict[str, Dict[str, float]]
    active_narrative_type: str
    active_narrative_text: str

def run_liquidity_crunch_experiment(
    calibration: ModelCalibration = CALIBRATED_MODELS["openai_gpt_tier"],
    tenor_days: int = 90,
    advertised_discount_pct: float = 0.15,
    num_paths: int = 25000,
    resale_window_days: int = 14,
    random_seed: int = 42,
    scenario: Optional[MarketScenario] = None,
    liquidity_cal: Optional[LiquidityCalibration] = None
) -> CrunchExperimentResult:
    sim = run_monte_carlo(
        calibration=calibration,
        tenor_days=tenor_days,
        num_paths=num_paths,
        resale_window_days=resale_window_days,
        random_seed=random_seed,
        scenario=scenario,
        liquidity_cal=liquidity_cal
    )
    
    s0 = calibration.spot_price_initial
    k_naive = s0 * (1.0 - advertised_discount_pct)
    f0 = sim.fair_forward_price
    
    shock_mask = sim.shock_mask
    normal_mask = ~shock_mask
    
    n_shock = int(np.sum(shock_mask))
    n_normal = int(np.sum(normal_mask))
    shock_prob = n_shock / num_paths
    
    s_term_normal = sim.terminal_spot[normal_mask]
    s_term_shock = sim.terminal_spot[shock_mask]
    
    p_resale_normal = sim.realized_resale_price[normal_mask]
    p_resale_shock = sim.realized_resale_price[shock_mask]
    
    mean_s_norm = float(np.mean(s_term_normal))
    mean_s_shock = float(np.mean(s_term_shock))
    
    mean_p_norm = float(np.mean(p_resale_normal))
    mean_p_shock = float(np.mean(p_resale_shock))
    
    f_unshocked_benchmark = mean_s_norm
    d_norm_bm_paths = (f_unshocked_benchmark - p_resale_normal) / f_unshocked_benchmark
    d_shock_bm_paths = (f_unshocked_benchmark - p_resale_shock) / f_unshocked_benchmark
    mean_d_norm_bm = float(np.mean(d_norm_bm_paths))
    mean_d_shock_bm = float(np.mean(d_shock_bm_paths))
    lcr_benchmark_point = mean_d_shock_bm / max(1e-6, mean_d_norm_bm)
    
    spread_norm_paths = (s_term_normal - p_resale_normal) / s_term_normal
    spread_shock_paths = (s_term_shock - p_resale_shock) / s_term_shock
    mean_spread_norm = float(np.mean(spread_norm_paths))
    mean_spread_shock = float(np.mean(spread_shock_paths))
    lcr_spread_point = mean_spread_shock / max(1e-6, mean_spread_norm)
    
    rng = np.random.default_rng(random_seed + 101)
    b_reps = 2000
    boot_lcr_bm = np.empty(b_reps, dtype=np.float64)
    boot_lcr_sp = np.empty(b_reps, dtype=np.float64)
    
    idx_normal = np.arange(n_normal)
    idx_shock = np.arange(n_shock)
    
    for b in range(b_reps):
        b_idx_norm = rng.choice(idx_normal, size=n_normal, replace=True)
        b_idx_shock = rng.choice(idx_shock, size=n_shock, replace=True)
        
        b_d_norm_bm = np.mean(d_norm_bm_paths[b_idx_norm])
        b_d_shock_bm = np.mean(d_shock_bm_paths[b_idx_shock])
        boot_lcr_bm[b] = b_d_shock_bm / max(1e-6, b_d_norm_bm)
        
        b_sp_norm = np.mean(spread_norm_paths[b_idx_norm])
        b_sp_shock = np.mean(spread_shock_paths[b_idx_shock])
        boot_lcr_sp[b] = b_sp_shock / max(1e-6, b_sp_norm)
    
    lcr_bm_ci_lower = float(np.percentile(boot_lcr_bm, 2.5))
    lcr_bm_ci_upper = float(np.percentile(boot_lcr_bm, 97.5))
    lcr_sp_ci_lower = float(np.percentile(boot_lcr_sp, 2.5))
    lcr_sp_ci_upper = float(np.percentile(boot_lcr_sp, 97.5))
    
    time_years = tenor_days / 365.0
    df = np.exp(-0.04 * time_years)
    
    p_resale_perfect_liq = sim.terminal_spot * (1.0 - calibration.base_spread)
    fair_cost_fwd_no_liq_paths = f0 - ((1.0 - sim.utilization) * p_resale_perfect_liq * df)
    fair_cost_fwd_actual_paths = f0 - ((1.0 - sim.utilization) * sim.realized_resale_price * df)
    spot_cost_paths = sim.utilization * sim.terminal_spot * df
    
    cost_spot_shock_mean = float(np.mean(spot_cost_paths[shock_mask]))
    cost_fwd_no_liq_shock_mean = float(np.mean(fair_cost_fwd_no_liq_paths[shock_mask]))
    cost_fwd_actual_shock_mean = float(np.mean(fair_cost_fwd_actual_paths[shock_mask]))
    
    total_shock_penalty = cost_fwd_actual_shock_mean - cost_spot_shock_mean
    total_shock_penalty_pct = (total_shock_penalty / max(1e-6, cost_spot_shock_mean)) * 100.0
    liquidity_blowout_penalty = cost_fwd_actual_shock_mean - cost_fwd_no_liq_shock_mean
    
    naive_cost_fwd_paths = k_naive - ((1.0 - sim.utilization) * sim.realized_resale_price * df)
    naive_exp_cost_fwd = float(np.mean(naive_cost_fwd_paths))
    naive_exp_cost_ondemand = float(np.mean(spot_cost_paths))
    naive_net_cost_penalty = naive_exp_cost_fwd - naive_exp_cost_ondemand
    naive_net_cost_penalty_pct = (naive_net_cost_penalty / max(1e-6, naive_exp_cost_ondemand)) * 100.0
    
    stress_scenarios = {}
    
    cal_freeze = ModelCalibration(
        provider=calibration.provider,
        family_name=calibration.family_name,
        spot_price_initial=calibration.spot_price_initial,
        annual_drift=calibration.annual_drift,
        annual_volatility=calibration.annual_volatility,
        hazard_rate_annual=calibration.hazard_rate_annual,
        jump_mean=calibration.jump_mean,
        base_spread=calibration.base_spread,
        shock_spread=0.65
    )
    sim_freeze = run_monte_carlo(cal_freeze, tenor_days, num_paths=num_paths, resale_window_days=resale_window_days, random_seed=random_seed)
    d_shock_bm_freeze = (f_unshocked_benchmark - sim_freeze.realized_resale_price[sim_freeze.shock_mask]) / f_unshocked_benchmark
    lcr_bm_freeze = float(np.mean(d_shock_bm_freeze)) / max(1e-6, mean_d_norm_bm)
    cost_fwd_freeze_sh = f0 - ((1.0 - sim_freeze.utilization[sim_freeze.shock_mask]) * sim_freeze.realized_resale_price[sim_freeze.shock_mask] * df)
    stress_scenarios["secondary_market_freeze"] = {
        "shock_spread": 0.65,
        "mean_resale_price": float(np.mean(sim_freeze.realized_resale_price[sim_freeze.shock_mask])),
        "lcr_benchmark": lcr_bm_freeze,
        "delta_vs_baseline_lcr": lcr_bm_freeze - lcr_benchmark_point,
        "shock_net_cost_forward": float(np.mean(cost_fwd_freeze_sh)),
        "shock_net_penalty": float(np.mean(cost_fwd_freeze_sh)) - cost_spot_shock_mean
    }
    
    rng_u = np.random.default_rng(random_seed + 505)
    u_shocked = rng_u.beta(a=1.5, b=6.0, size=num_paths)
    cost_fwd_u_sh = f0 - ((1.0 - u_shocked[shock_mask]) * sim.realized_resale_price[shock_mask] * df)
    cost_spot_u_sh = u_shocked[shock_mask] * sim.terminal_spot[shock_mask] * df
    exp_cost_fwd_u_sh = float(np.mean(cost_fwd_u_sh))
    exp_cost_spot_u_sh = float(np.mean(cost_spot_u_sh))
    stress_scenarios["buyer_utilization_collapse"] = {
        "mean_utilization": float(np.mean(u_shocked)),
        "shock_net_cost_forward": exp_cost_fwd_u_sh,
        "shock_net_cost_ondemand": exp_cost_spot_u_sh,
        "shock_penalty": exp_cost_fwd_u_sh - exp_cost_spot_u_sh,
        "shock_penalty_pct": ((exp_cost_fwd_u_sh - exp_cost_spot_u_sh) / max(1e-6, exp_cost_spot_u_sh)) * 100.0
    }
    
    cal_release_war = ModelCalibration(
        provider=calibration.provider,
        family_name=calibration.family_name,
        spot_price_initial=calibration.spot_price_initial,
        annual_drift=calibration.annual_drift,
        annual_volatility=calibration.annual_volatility,
        hazard_rate_annual=calibration.hazard_rate_annual * 2.0,
        jump_mean=calibration.jump_mean,
        base_spread=calibration.base_spread,
        shock_spread=calibration.shock_spread
    )
    sim_war = run_monte_carlo(cal_release_war, tenor_days, num_paths=num_paths, resale_window_days=resale_window_days, random_seed=random_seed)
    n_shock_war = int(np.sum(sim_war.shock_mask))
    cost_fwd_war_sh = f0 - ((1.0 - sim_war.utilization[sim_war.shock_mask]) * sim_war.realized_resale_price[sim_war.shock_mask] * df)
    cost_spot_war_sh = sim_war.utilization[sim_war.shock_mask] * sim_war.terminal_spot[sim_war.shock_mask] * df
    stress_scenarios["frontier_release_war"] = {
        "hazard_rate_annual": cal_release_war.hazard_rate_annual,
        "shock_probability": n_shock_war / num_paths,
        "shock_net_cost_forward": float(np.mean(cost_fwd_war_sh)),
        "shock_net_cost_ondemand": float(np.mean(cost_spot_war_sh)),
        "shock_penalty": float(np.mean(cost_fwd_war_sh)) - float(np.mean(cost_spot_war_sh))
    }
    
    if lcr_benchmark_point >= 1.50 and total_shock_penalty > 0:
        active_narrative_type = "material_crunch"
        active_narrative_text = (
            f"Under correlated frontier release shocks, Touchmark's secondary resale mechanism experiences a "
            f"structural liquidity crunch. The primary Benchmark Liquidity Crunch Ratio reaches {lcr_benchmark_point:.2f}x "
            f"(95% CI: [{lcr_bm_ci_lower:.2f}x, {lcr_bm_ci_upper:.2f}x]), while the microstructural spread ratio expands to {lcr_spread_point:.2f}x "
            f"(95% CI: [{lcr_sp_ci_lower:.2f}x, {lcr_sp_ci_upper:.2f}x]). When evaluated at the engine's fair forward price ($3.62/M), "
            f"a buyer caught in a shock window pays an expected net cost of ${cost_fwd_actual_shock_mean:.3f}/M versus ${cost_spot_shock_mean:.3f}/M "
            f"on spot—a +{total_shock_penalty_pct:.1f}% shock penalty (+${total_shock_penalty:.3f}/M), with secondary market spread blowout "
            f"accounting for +${liquidity_blowout_penalty:.3f}/M of direct liquidation loss."
        )
    else:
        active_narrative_type = "contained_variance"
        active_narrative_text = (
            f"While secondary market spreads widen during generational model releases, the primary Liquidity Crunch Ratio "
            f"remains contained at {lcr_benchmark_point:.2f}x (95% CI: [{lcr_bm_ci_lower:.2f}x, {lcr_bm_ci_upper:.2f}x]). "
            f"The secondary market maintains sufficient depth to absorb liquidations without severe price collapse, "
            f"with resale discounts averaging {mean_spread_shock:.1%} during shock windows versus {mean_spread_norm:.1%} under normal operations."
        )
    
    return CrunchExperimentResult(
        calibration=calibration,
        tenor_days=tenor_days,
        num_paths=num_paths,
        initial_spot=s0,
        advertised_discount_pct=advertised_discount_pct,
        strike_price_naive=k_naive,
        fair_forward_price=f0,
        num_shock_paths=n_shock,
        num_normal_paths=n_normal,
        shock_prob_empirical=shock_prob,
        mean_spot_normal=mean_s_norm,
        mean_spot_shock=mean_s_shock,
        mean_resale_normal=mean_p_norm,
        mean_resale_shock=mean_p_shock,
        resale_spread_normal=mean_spread_norm,
        resale_spread_shock=mean_spread_shock,
        lcr_benchmark=lcr_benchmark_point,
        lcr_benchmark_ci_lower=lcr_bm_ci_lower,
        lcr_benchmark_ci_upper=lcr_bm_ci_upper,
        lcr_spread=lcr_spread_point,
        lcr_spread_ci_lower=lcr_sp_ci_lower,
        lcr_spread_ci_upper=lcr_sp_ci_upper,
        fair_cost_spot_shock=cost_spot_shock_mean,
        fair_cost_fwd_no_liq_shock=cost_fwd_no_liq_shock_mean,
        fair_cost_fwd_actual_shock=cost_fwd_actual_shock_mean,
        fair_total_shock_penalty=total_shock_penalty,
        fair_total_shock_penalty_pct=total_shock_penalty_pct,
        fair_liquidity_blowout_penalty=liquidity_blowout_penalty,
        naive_expected_net_cost_forward=naive_exp_cost_fwd,
        naive_expected_cost_ondemand=naive_exp_cost_ondemand,
        naive_net_cost_penalty=naive_net_cost_penalty,
        naive_net_cost_penalty_pct=naive_net_cost_penalty_pct,
        stress_scenarios=stress_scenarios,
        active_narrative_type=active_narrative_type,
        active_narrative_text=active_narrative_text
    )

def run_data_driven_crunch_comparison(
    calibration: ModelCalibration = CALIBRATED_MODELS["openai_gpt_tier"],
    tenor_days: int = 90,
    num_paths: int = 25000,
    random_seed: int = 42
) -> Dict[str, Any]:
    res_assumed = run_liquidity_crunch_experiment(
        calibration=calibration,
        tenor_days=tenor_days,
        num_paths=num_paths,
        random_seed=random_seed,
        scenario=MarketScenario(contract_type="assumed")
    )
    
    empirical_phi_samples = np.array([0.817, 0.416, 0.470, 0.094, 0.683, 1.000])
    sc_empirical = MarketScenario(
        switch_share=float(np.mean(empirical_phi_samples)),
        switch_share_samples=empirical_phi_samples,
        contract_type="specific"
    )
    res_data_driven = run_liquidity_crunch_experiment(
        calibration=calibration,
        tenor_days=tenor_days,
        num_paths=num_paths,
        random_seed=random_seed,
        scenario=sc_empirical
    )
    
    conversion_rates = [0.0, 0.25, 0.50, 0.75, 1.0]
    conversion_curve = []
    for c_rate in conversion_rates:
        sc_conv = MarketScenario(
            switch_share=float(np.mean(empirical_phi_samples)),
            switch_share_samples=empirical_phi_samples,
            conversion_rate=c_rate,
            contract_type="specific"
        )
        res_c = run_liquidity_crunch_experiment(
            calibration=calibration,
            tenor_days=tenor_days,
            num_paths=15000,
            random_seed=random_seed,
            scenario=sc_conv
        )
        conversion_curve.append({
            "conversion_rate_pct": round(c_rate * 100, 1),
            "lcr_benchmark": round(res_c.lcr_benchmark, 2),
            "lcr_spread": round(res_c.lcr_spread, 2),
            "shock_spread_pct": round(res_c.resale_spread_shock * 100, 1),
            "total_shock_penalty": round(res_c.fair_total_shock_penalty, 3)
        })
    
    daily_vols = [0.005, 0.01, 0.02, 0.03, 0.05]
    impact_powers = [0.5, 0.75, 1.0]
    heatmap_grid = []
    for v_daily in daily_vols:
        row = []
        for p_pow in impact_powers:
            liq = LiquidityCalibration(
                base_spread=calibration.base_spread,
                shock_spread_target=calibration.shock_spread,
                impact_exponent=p_pow,
                daily_volume_ratio=v_daily
            )
            res_hm = run_liquidity_crunch_experiment(
                calibration=calibration,
                tenor_days=tenor_days,
                num_paths=10000,
                random_seed=random_seed,
                scenario=sc_empirical,
                liquidity_cal=liq
            )
            row.append(round(res_hm.lcr_benchmark, 2))
        heatmap_grid.append(row)
    
    return {
        "assumed_scenario": {
            "lcr_benchmark": round(res_assumed.lcr_benchmark, 2),
            "lcr_ci": [round(res_assumed.lcr_benchmark_ci_lower, 2), round(res_assumed.lcr_benchmark_ci_upper, 2)],
            "lcr_spread": round(res_assumed.lcr_spread, 2),
            "spread_shock_pct": round(res_assumed.resale_spread_shock * 100, 1),
            "shock_penalty": round(res_assumed.fair_total_shock_penalty, 3),
            "mean_resale_shock": round(res_assumed.mean_resale_shock, 2)
        },
        "data_driven_scenario": {
            "lcr_benchmark": round(res_data_driven.lcr_benchmark, 2),
            "lcr_ci": [round(res_data_driven.lcr_benchmark_ci_lower, 2), round(res_data_driven.lcr_benchmark_ci_upper, 2)],
            "lcr_spread": round(res_data_driven.lcr_spread, 2),
            "spread_shock_pct": round(res_data_driven.resale_spread_shock * 100, 1),
            "shock_penalty": round(res_data_driven.fair_total_shock_penalty, 3),
            "mean_resale_shock": round(res_data_driven.mean_resale_shock, 2),
            "empirical_mean_phi": round(float(np.mean(empirical_phi_samples)), 3)
        },
        "conversion_curve": conversion_curve,
        "heatmap": {
            "daily_vols_pct": [round(v * 100, 1) for v in daily_vols],
            "impact_exponents": impact_powers,
            "grid_lcr": heatmap_grid
        }
    }
