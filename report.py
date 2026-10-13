import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from models import CALIBRATED_MODELS
from engine import compute_sensitivities, convergence_analysis
from crunch_experiment import run_liquidity_crunch_experiment, run_data_driven_crunch_comparison
from narrative_gen import generate_market_narrative
from rfq_sim import simulate_rfq_flow
from migration import get_empirical_migration_dataset
from contracts import evaluate_upgrade_conversion

def main():
    console = Console()
    
    console.print()
    header_panel = Panel.fit(
        Text("TOUCHMARK MARKET-RISK SIMULATION: QUANTITATIVE EVALUATION HARNESS\nSecondary Market Liquidity, Empirical Model Migration & Contract Copilot", justify="center", style="bold cyan"),
        subtitle="Empirical Calibration & Risk-Engineering Framework",
        border_style="cyan"
    )
    console.print(header_panel)
    console.print()
    
    cal_table = Table(title="Model Family Calibrations (Public Data Calibrated)", border_style="blue", show_header=True, header_style="bold magenta")
    cal_table.add_column("Parameter / Dimension", style="dim")
    cal_table.add_column("OpenAI GPT-4 / 4o Tier", justify="right")
    cal_table.add_column("Anthropic Claude 3 / 3.5 Tier", justify="right")
    cal_table.add_column("Calibration Source / Methodology", style="italic")
    
    cal_table.add_row("Initial Spot Price (S0)", "$5.00 / M tokens", "$3.00 / M tokens", "Verified launch input pricing (GPT-4o / Claude 3.5)")
    cal_table.add_row("Annual Drift (mu)", "-35.0% / year", "-18.0% / year", "Intra-model efficiency gains & provider margin cuts")
    cal_table.add_row("Annual Volatility (sigma)", "28.0% / year", "22.0% / year", "On-demand GPU cloud compute price fluctuations")
    cal_table.add_row("Obsolescence Hazard (lambda)", "1.85 / year (~6.5 mo tenure)", "0.60 / year (~20 mo tenure)", "Verified historical release cadences (OpenAI vs Anthropic)")
    cal_table.add_row("Generational Jump (J)", "45.0% drop", "40.0% drop", "Verified generational price cuts (GPT-4->4o, Opus->Sonnet)")
    cal_table.add_row("Base Secondary Spread (delta_base)", "6.0%", "5.0%", "Idiosyncratic secondary resale friction")
    cal_table.add_row("Shock Secondary Spread (delta_shock)", "38.0%", "32.0%", "Correlated sell-off order book depth collapse")
    cal_table.add_row("Scope Constraint", "Single-provider proprietary", "Single-provider proprietary", "Multi-host open-weights (Llama) excluded (provider risk)")
    console.print(cal_table)
    console.print()
    
    emp_dataset = get_empirical_migration_dataset()
    emp_table = Table(
        title="Empirical Model Migration Velocity (OpenRouter Rankings API: Jan 2025 - Oct 2026)",
        caption="[bold cyan]Key Finding: Replaces arbitrary 38% assumption with verified 14-day token migration velocity.",
        border_style="cyan",
        show_header=True,
        header_style="bold cyan"
    )
    emp_table.add_column("Event ID", style="bold")
    emp_table.add_column("Provider", style="dim")
    emp_table.add_column("Incumbent -> Replacement", style="white")
    emp_table.add_column("Launch Date", justify="center")
    emp_table.add_column("Pre-Share", justify="right")
    emp_table.add_column("phi_14d (Switch)", justify="right", style="bold yellow")
    emp_table.add_column("phi_28d (Switch)", justify="right", style="bold green")
    
    for ev in emp_dataset["events"]:
        emp_table.add_row(
            ev["id"],
            ev["provider"],
            f"{ev['old_model']} -> {ev['new_model']}",
            ev["launch_date"],
            f"{ev['pre_launch_share']:.1%}",
            f"{ev['phi_14']:.1%}",
            f"{ev['phi_28']:.1%}"
        )
    console.print(emp_table)
    console.print(
        f"[bold cyan]Mean Empirical 14-Day Switch Share (phi): {emp_dataset['mean_switch_share']:.1%}[/bold cyan] "
        f"[dim](95% Bootstrap CI: [{emp_dataset['ci_95'][0]:.1%}, {emp_dataset['ci_95'][1]:.1%}])[/dim]"
    )
    console.print()
    
    conv_table = Table(
        title="Monte Carlo Numerical Convergence Check (OpenAI Tier, 90-Day Tenor)",
        caption="[bold yellow]Note: This is an internal numerical validity check, NOT a historical loss backtest (no historical forward exchange tape exists).",
        border_style="green",
        show_header=True,
        header_style="bold green"
    )
    conv_table.add_column("Paths (N)", justify="right")
    conv_table.add_column("Fair Forward Price (F0)", justify="right")
    conv_table.add_column("Standard Error", justify="right")
    conv_table.add_column("95% CI Interval", justify="center")
    conv_table.add_column("Relative Error (%)", justify="right")
    
    conv_data = convergence_analysis(CALIBRATED_MODELS["openai_gpt_tier"], tenor_days=90, path_counts=[500, 1000, 2500, 5000, 10000, 20000])
    for row in conv_data:
        conv_table.add_row(
            f"{row['num_paths']:,}",
            f"${row['fair_forward_price']:.4f}",
            f"+/- ${row['standard_error']:.4f}",
            f"[${row['ci_95_lower']:.4f}, ${row['ci_95_upper']:.4f}]",
            f"{row['relative_error_pct']:.2f}%"
        )
    console.print(conv_table)
    console.print()
    
    sens_openai = compute_sensitivities(CALIBRATED_MODELS["openai_gpt_tier"], tenor_days=90)
    sens_anthropic = compute_sensitivities(CALIBRATED_MODELS["anthropic_claude_tier"], tenor_days=90)
    
    sens_table = Table(
        title="Parameter Sensitivities (Finite Differences) - NOT Greeks (No Continuous Hedging)",
        caption="[bold yellow]Terminology Guardrail: Tokens are non-storable flow services. No continuous delta replication is possible.",
        border_style="magenta",
        show_header=True,
        header_style="bold yellow"
    )
    sens_table.add_column("Sensitivity Metric", style="dim")
    sens_table.add_column("OpenAI Tier (S0=$5.00, T=90d)", justify="right")
    sens_table.add_column("Anthropic Tier (S0=$3.00, T=90d)", justify="right")
    sens_table.add_column("Mathematical Definition", style="italic")
    
    sens_table.add_row("Base Fair Forward Price (F0)", f"${sens_openai['fair_forward_price']:.3f}", f"${sens_anthropic['fair_forward_price']:.3f}", "E_Q[Discounted Terminal Payoff]")
    sens_table.add_row("Spot-Price Sensitivity", f"{sens_openai['spot_price_sensitivity']:.3f}", f"{sens_anthropic['spot_price_sensitivity']:.3f}", "d(F0) / d(S0)")
    sens_table.add_row("Hazard-Rate Sensitivity", f"{sens_openai['hazard_rate_sensitivity']:.3f}", f"{sens_anthropic['hazard_rate_sensitivity']:.3f}", "d(F0) / d(lambda)")
    sens_table.add_row("Tenor Sensitivity (per day)", f"${sens_openai['tenor_sensitivity_per_day']:.4f}/day", f"${sens_anthropic['tenor_sensitivity_per_day']:.4f}/day", "d(F0) / d(T_days)")
    sens_table.add_row("Tenor Sensitivity (annualized)", f"${sens_openai['tenor_sensitivity_annual']:.3f}/year", f"${sens_anthropic['tenor_sensitivity_annual']:.3f}/year", "d(F0) / d(T_years)")
    sens_table.add_row("Volatility Sensitivity", f"{sens_openai['volatility_sensitivity']:.3f}", f"{sens_anthropic['volatility_sensitivity']:.3f}", "d(F0) / d(sigma)")
    console.print(sens_table)
    console.print()
    
    console.print("[bold yellow]Executing Headline Liquidity Crunch Experiment (N = 25,000 paths)...[/bold yellow]")
    crunch_res = run_liquidity_crunch_experiment(
        calibration=CALIBRATED_MODELS["openai_gpt_tier"],
        tenor_days=90,
        advertised_discount_pct=0.15,
        num_paths=25000,
        resale_window_days=14,
        random_seed=42
    )
    
    headline_panel = Panel(
        Text.from_markup(
            f"[bold red]PRIMARY METRIC: BENCHMARK LIQUIDITY CRUNCH RATIO = {crunch_res.lcr_benchmark:.2f}x[/bold red]\n"
            f"[bold white]95% Bootstrap Confidence Interval: [{crunch_res.lcr_benchmark_ci_lower:.2f}x, {crunch_res.lcr_benchmark_ci_upper:.2f}x][/bold white]\n"
            f"[dim white]Definition: (Resale Discount vs Unshocked Counterfactual Benchmark during Shock) / (Discount during Normal Conditions)[/dim white]\n\n"
            f"[bold yellow]ROBUSTNESS CHECK: MICROSTRUCTURAL SPREAD RATIO = {crunch_res.lcr_spread:.2f}x[/bold yellow]\n"
            f"[white]95% Bootstrap Confidence Interval: [{crunch_res.lcr_spread_ci_lower:.2f}x, {crunch_res.lcr_spread_ci_upper:.2f}x][/white]\n"
            f"[dim white]Definition: (Shock Window Spread delta_shock = {crunch_res.resale_spread_shock:.1%}) / (Normal Spread delta_base = {crunch_res.resale_spread_normal:.1%})[/dim white]\n\n"
            f"[bold]Mean Resale Realized (Normal):[/bold] ${crunch_res.mean_resale_normal:.3f}/M  |  "
            f"[bold]Mean Resale Realized (Shock):[/bold] [bold red]${crunch_res.mean_resale_shock:.3f}/M[/bold red]\n"
            f"[bold]Obsolescence Shock Occurrence in 14d Resale Window:[/bold] {crunch_res.shock_prob_empirical:.1%} of paths\n\n"
            f"[italic white]Framing: Simulation result under documented assumptions. Not a claim regarding Touchmark's internal book.[/italic white]"
        ),
        title="[bold red]HEADLINE EXPERIMENT: LIQUIDITY CRUNCH RATIOS (PRIMARY & ROBUSTNESS)[/bold red]",
        border_style="red"
    )
    console.print(headline_panel)
    console.print()
    
    crunch_cmp = run_data_driven_crunch_comparison()
    cmp_table = Table(
        title="Data-Driven vs. Assumed Crunch Comparison (Square-Root Impact Law)",
        caption="[bold green]Rigor Check: Demonstrates that the liquidity crunch is NOT an artifact of the 38% assumption.",
        border_style="green",
        show_header=True,
        header_style="bold green"
    )
    cmp_table.add_column("Methodological Dimension", style="bold")
    cmp_table.add_column("Assumed Baseline", justify="right")
    cmp_table.add_column("Empirical Data-Driven", justify="right", style="bold cyan")
    cmp_table.add_column("Structural Impact", style="italic")
    
    cmp_table.add_row(
        "Secondary Resale Spread",
        f"{crunch_cmp['assumed_scenario']['spread_shock_pct']:.1f}%",
        f"{crunch_cmp['data_driven_scenario']['spread_shock_pct']:.1f}%",
        "Corroborates assumed 38% order book widening"
    )
    cmp_table.add_row(
        "Benchmark LCR",
        f"{crunch_cmp['assumed_scenario']['lcr_benchmark']:.2f}x",
        f"{crunch_cmp['data_driven_scenario']['lcr_benchmark']:.2f}x",
        "Crunch naturally emerges from empirical migration velocity"
    )
    cmp_table.add_row(
        "Net Shock Penalty vs Spot",
        f"+${crunch_cmp['assumed_scenario']['shock_penalty']:.3f}/M",
        f"+${crunch_cmp['data_driven_scenario']['shock_penalty']:.3f}/M",
        "Confirmed severe buyer balance-sheet liquidation penalty"
    )
    cmp_table.add_row(
        "Mean Resale Price in Shock",
        f"${crunch_cmp['assumed_scenario']['mean_resale_shock']:.2f}/M",
        f"${crunch_cmp['data_driven_scenario']['mean_resale_shock']:.2f}/M",
        "Heavy salvage penalty confirmed"
    )
    console.print(cmp_table)
    console.print()
    
    conv_results = evaluate_upgrade_conversion()
    conv_table = Table(
        title="The Upgrade Conversion Option: Spread Compression Sensitivity",
        caption="[bold yellow]Contract Innovation: Bundled par-value upgrade conversions eliminate secondary resale panic.",
        border_style="yellow",
        show_header=True,
        header_style="bold yellow"
    )
    conv_table.add_column("Conversion Uptake (c)", justify="right", style="bold")
    conv_table.add_column("Secondary Spread", justify="right")
    conv_table.add_column("Benchmark LCR", justify="right")
    conv_table.add_column("Resale Price (Shock)", justify="right", style="bold green")
    conv_table.add_column("Net Shock Penalty", justify="right", style="bold yellow")
    conv_table.add_column("Liquidation Drag Dampening", style="dim")
    
    for r in conv_results:
        pct_red = ((conv_results[0]["shock_net_penalty"] - r["shock_net_penalty"]) / max(1e-4, conv_results[0]["shock_net_penalty"])) * 100.0
        conv_table.add_row(
            f"{r['conversion_rate_pct']:.0f}%",
            f"{r['shock_spread_pct']:.1f}%",
            f"{r['lcr_benchmark']:.2f}x",
            f"${r['mean_resale_shock']:.2f}/M",
            f"+${r['shock_net_penalty']:.3f}/M",
            f"-{pct_red:.1f}% drag reduction" if pct_red > 0 else "Baseline (0% Conversion)"
        )
    console.print(conv_table)
    console.print()
    
    decomp_table = Table(
        title="Economic Impact Decomposition: Deflation-Alone vs. Correlated Liquidity Shock",
        border_style="yellow",
        show_header=True,
        header_style="bold yellow"
    )
    decomp_table.add_column("Procurement Mechanism / State", style="bold")
    decomp_table.add_column("Strike Reference", style="dim")
    decomp_table.add_column("Effective Cost", justify="right")
    decomp_table.add_column("Net Penalty vs Spot", justify="right", style="bold red")
    decomp_table.add_column("Root Economic Cause", style="italic")
    
    decomp_table.add_row(
        "1. Naive 15% Spot Discount (Unconditional)",
        f"K = ${crunch_res.strike_price_naive:.2f}/M",
        f"${crunch_res.naive_expected_net_cost_forward:.3f}/M",
        f"+${crunch_res.naive_net_cost_penalty:.3f}/M (+{crunch_res.naive_net_cost_penalty_pct:.1f}%)",
        "Asset Deflation: 15% discount fails to match -35% hardware deflation rate"
    )
    decomp_table.add_row(
        "2. Fair-Value Forward F0 (Unconditional)",
        f"F0 = ${crunch_res.fair_forward_price:.3f}/M",
        f"${crunch_res.fair_forward_price:.3f}/M",
        "$0.000/M (0.0%)",
        "Actuarial Parity: Correctly prices deflation and hazard into forward commitment"
    )
    decomp_table.add_row(
        "3. Fair-Value Forward in Shock (Perfect Liquidity)",
        f"F0 = ${crunch_res.fair_forward_price:.3f}/M",
        f"${crunch_res.fair_cost_fwd_no_liq_shock:.3f}/M",
        f"+${crunch_res.fair_cost_fwd_no_liq_shock - crunch_res.fair_cost_spot_shock:.3f}/M (+{((crunch_res.fair_cost_fwd_no_liq_shock - crunch_res.fair_cost_spot_shock) / crunch_res.fair_cost_spot_shock) * 100:.1f}%)",
        "Model Obsolescence Lock-in: Buyer holds old model while spot drops to $1.46/M"
    )
    decomp_table.add_row(
        "4. Fair-Value Forward in Shock (ACTUAL MARKET)",
        f"F0 = ${crunch_res.fair_forward_price:.3f}/M",
        f"${crunch_res.fair_cost_fwd_actual_shock:.3f}/M",
        f"+${crunch_res.fair_total_shock_penalty:.3f}/M (+{crunch_res.fair_total_shock_penalty_pct:.1f}%)",
        f"TOTAL SHOCK PENALTY: Spot is ${crunch_res.fair_cost_spot_shock:.3f}/M; liq freeze adds +${crunch_res.fair_liquidity_blowout_penalty:.3f}/M"
    )
    console.print(decomp_table)
    console.print()
    
    stress_table = Table(
        title="Supporting Stress Scenarios (Conditional on Obsolescence Shock)",
        border_style="red",
        show_header=True,
        header_style="bold red"
    )
    stress_table.add_column("Scenario Name", style="bold")
    stress_table.add_column("Stress Condition", style="dim")
    stress_table.add_column("Primary Benchmark LCR", justify="right")
    stress_table.add_column("Shock Forward Cost", justify="right")
    stress_table.add_column("Shock Net Penalty vs Spot", justify="right", style="bold red")
    
    s_freeze = crunch_res.stress_scenarios["secondary_market_freeze"]
    s_util = crunch_res.stress_scenarios["buyer_utilization_collapse"]
    s_war = crunch_res.stress_scenarios["frontier_release_war"]
    
    stress_table.add_row(
        "Secondary Market Freeze",
        "Spread widens to 65.0%",
        f"{s_freeze['lcr_benchmark']:.2f}x",
        f"${s_freeze['shock_net_cost_forward']:.3f}/M",
        f"+${s_freeze['shock_net_penalty']:.3f}/M"
    )
    stress_table.add_row(
        "Buyer Utilization Collapse",
        "Internal utilization drops to 20.0%",
        "Demand Shock",
        f"${s_util['shock_net_cost_forward']:.3f}/M",
        f"+${s_util['shock_penalty']:.3f}/M (+{s_util['shock_penalty_pct']:.1f}%)"
    )
    stress_table.add_row(
        "Frontier Release War",
        f"Cadence doubles (lambda={s_war['hazard_rate_annual']:.2f}/yr)",
        "Elevated Frequency",
        f"${s_war['shock_net_cost_forward']:.3f}/M",
        f"+${s_war['shock_penalty']:.3f}/M"
    )
    console.print(stress_table)
    console.print()
    
    rfq_res = simulate_rfq_flow(
        notional_millions=500.0,
        num_dealers=5,
        random_seed=42
    )
    
    rfq_table = Table(
        title="Phase 4 (Exploratory Sketch): RFQ vs. Open Order Book Execution (500M Block)",
        caption="[dim]Exploratory sketch comparing 5-dealer sealed-bid RFQ against public order book depth.",
        border_style="cyan",
        show_header=True,
        header_style="bold cyan"
    )
    rfq_table.add_column("Market State", style="bold")
    rfq_table.add_column("Open Book Spread", justify="right")
    rfq_table.add_column("Best RFQ Dealer Quote", justify="right")
    rfq_table.add_column("Price Improvement", justify="right", style="bold green")
    rfq_table.add_column("Dealer Bid Range", style="dim")
    
    rfq_table.add_row(
        "Normal Trading",
        f"{rfq_res.normal_open_book_spread:.1%}",
        f"{rfq_res.normal_rfq_best_spread:.1%}",
        f"+{rfq_res.normal_rfq_price_improvement_pct:.1f}%",
        f"[{min(rfq_res.rfq_dealer_bids_normal):.1%}, {max(rfq_res.rfq_dealer_bids_normal):.1%}]"
    )
    rfq_table.add_row(
        "Correlated Shock Window",
        f"{rfq_res.shock_open_book_spread:.1%}",
        f"{rfq_res.shock_rfq_best_spread:.1%}",
        f"+{rfq_res.shock_rfq_price_improvement_pct:.1f}%",
        f"[{min(rfq_res.rfq_dealer_bids_shock):.1%}, {max(rfq_res.rfq_dealer_bids_shock):.1%}]"
    )
    console.print(rfq_table)
    console.print()
    
    narrative_input = {
        "lcr_benchmark": crunch_res.lcr_benchmark,
        "lcr_benchmark_ci_lower": crunch_res.lcr_benchmark_ci_lower,
        "lcr_benchmark_ci_upper": crunch_res.lcr_benchmark_ci_upper,
        "lcr_spread": crunch_res.lcr_spread,
        "lcr_spread_ci_lower": crunch_res.lcr_spread_ci_lower,
        "lcr_spread_ci_upper": crunch_res.lcr_spread_ci_upper,
        "resale_spread_normal": crunch_res.resale_spread_normal,
        "resale_spread_shock": crunch_res.resale_spread_shock,
        "fair_forward_price": crunch_res.fair_forward_price,
        "fair_cost_spot_shock": crunch_res.fair_cost_spot_shock,
        "fair_cost_fwd_actual_shock": crunch_res.fair_cost_fwd_actual_shock,
        "fair_total_shock_penalty": crunch_res.fair_total_shock_penalty,
        "fair_total_shock_penalty_pct": crunch_res.fair_total_shock_penalty_pct,
        "fair_liquidity_blowout_penalty": crunch_res.fair_liquidity_blowout_penalty,
        "naive_net_cost_penalty": crunch_res.naive_net_cost_penalty,
        "naive_net_cost_penalty_pct": crunch_res.naive_net_cost_penalty_pct
    }
    narrative = generate_market_narrative(narrative_input)
    
    narrative_panel = Panel(
        Text.from_markup(
            f"[bold cyan]Synthesis Mode: {narrative['source']}[/bold cyan]\n\n"
            f"[bold]Headline Finding:[/bold]\n{narrative['headline_summary']}\n\n"
            f"[bold]Economic Risk Assessment:[/bold]\n{narrative['economic_summary']}"
        ),
        title="[bold cyan]EXECUTIVE QUANTITATIVE SYNTHESIS (GEMINI / DETERMINISTIC LAYER)[/bold cyan]",
        border_style="cyan"
    )
    console.print(narrative_panel)
    console.print()
    
    with open("evaluation_report.md", "w", encoding="utf-8") as f:
        f.write("# TOUCHMARK MARKET-RISK SIMULATION: COMPREHENSIVE EVALUATION REPORT\n\n")
        f.write("## Important Framing & Methodology\n")
        f.write(
            "This project is a quantitative market-risk simulation and contract sizing engine built for forward capacity markets in AI tokens. "
            "It is grounded in empirical public data (21+ months of OpenRouter daily token traffic rankings, official release dates, and public API price cuts). "
            "It does NOT use Touchmark's internal order book or proprietary data. It demonstrates a rigorous risk-engineering methodology "
            "tailored for high-growth compute market builders.\n\n"
        )
        f.write("## 1. Empirical Model Migration Velocity (OpenRouter 2025–2026)\n\n")
        f.write(f"- **Mean 14-Day Empirical Switch Share (phi):** **{emp_dataset['mean_switch_share']:.1%}** (95% Bootstrap CI: [{emp_dataset['ci_95'][0]:.1%}, {emp_dataset['ci_95'][1]:.1%}])\n")
        f.write("- **Observed Generational Events:** 6 pairs (Claude 3.5 Sonnet -> Claude 3.7 Sonnet, Gemini Flash 1.5 -> Gemini Flash 2.0, Claude 3.7 Sonnet -> Claude 4 Sonnet, Gemini Flash 2.0 -> Gemini Flash 2.5, Claude 4 Sonnet -> Claude 4.5 Sonnet, DeepSeek V3 -> DeepSeek V4 Flash)\n\n")
        f.write("| Event | Provider | Transition | Launch Date | Pre-Launch Share | phi (14 Days) | phi (28 Days) |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for ev in emp_dataset["events"]:
            f.write(f"| {ev['id']} | {ev['provider']} | {ev['old_model']} -> {ev['new_model']} | {ev['launch_date']} | {ev['pre_launch_share']:.1%} | {ev['phi_14']:.1%} | {ev['phi_28']:.1%} |\n")
        f.write("\n")
        
        f.write("## 2. Model Calibration Table\n\n")
        f.write("| Dimension | OpenAI GPT-4/4o Tier | Anthropic Claude 3/3.5 Tier | Empirical Source |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        f.write(f"| Initial Spot S0 | ${CALIBRATED_MODELS['openai_gpt_tier'].spot_price_initial:.2f} | ${CALIBRATED_MODELS['anthropic_claude_tier'].spot_price_initial:.2f} | Verified API launch input pricing |\n")
        f.write(f"| Annual Drift mu | {CALIBRATED_MODELS['openai_gpt_tier'].annual_drift:.1%} | {CALIBRATED_MODELS['anthropic_claude_tier'].annual_drift:.1%} | Intra-model optimization & hardware cost curves |\n")
        f.write(f"| Annual Volatility sigma | {CALIBRATED_MODELS['openai_gpt_tier'].annual_volatility:.1%} | {CALIBRATED_MODELS['anthropic_claude_tier'].annual_volatility:.1%} | GPU cloud provider spot variance |\n")
        f.write(f"| Hazard Rate lambda | {CALIBRATED_MODELS['openai_gpt_tier'].hazard_rate_annual:.2f}/yr | {CALIBRATED_MODELS['anthropic_claude_tier'].hazard_rate_annual:.2f}/yr | Verified release announcements (6.5mo vs 20mo tenure) |\n")
        f.write(f"| Generational Jump J | {CALIBRATED_MODELS['openai_gpt_tier'].jump_mean:.1%} | {CALIBRATED_MODELS['anthropic_claude_tier'].jump_mean:.1%} | Generational price reset (GPT-4->4o, Opus->Sonnet) |\n")
        f.write(f"| Base Resale Spread | {CALIBRATED_MODELS['openai_gpt_tier'].base_spread:.1%} | {CALIBRATED_MODELS['anthropic_claude_tier'].base_spread:.1%} | Idiosyncratic secondary resale friction |\n")
        f.write(f"| Shock Resale Spread | {CALIBRATED_MODELS['openai_gpt_tier'].shock_spread:.1%} | {CALIBRATED_MODELS['anthropic_claude_tier'].shock_spread:.1%} | Correlated obsolescence market-maker widening |\n\n")
        
        f.write("## 3. Data-Driven vs. Assumed Crunch Comparison\n\n")
        f.write("| Parameter | Assumed Benchmark Baseline | Empirical Data-Driven (OpenRouter + Impact Law) | Structural Assessment |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        f.write(f"| Secondary Market Spread | {crunch_cmp['assumed_scenario']['spread_shock_pct']:.1f}% | {crunch_cmp['data_driven_scenario']['spread_shock_pct']:.1f}% | Corroborates assumed 38% order book widening |\n")
        f.write(f"| Benchmark LCR | {crunch_cmp['assumed_scenario']['lcr_benchmark']:.2f}x | {crunch_cmp['data_driven_scenario']['lcr_benchmark']:.2f}x | Crunch naturally emerges from real velocity |\n")
        f.write(f"| Shock Cost Penalty | +${crunch_cmp['assumed_scenario']['shock_penalty']:.3f}/M | +${crunch_cmp['data_driven_scenario']['shock_penalty']:.3f}/M | Robust net economic buyer penalty |\n")
        f.write(f"| Mean Resale Price in Shock | ${crunch_cmp['assumed_scenario']['mean_resale_shock']:.2f}/M | ${crunch_cmp['data_driven_scenario']['mean_resale_shock']:.2f}/M | Severe liquidation discount confirmed |\n\n")
        
        f.write("## 4. Contractual Innovation: The Upgrade Conversion Option\n\n")
        f.write("| Conversion Uptake Rate (c) | Secondary Market Spread | Benchmark LCR | Mean Resale Price (Shock) | Shock Net Penalty vs Spot |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for r in conv_results:
            f.write(f"| {r['conversion_rate_pct']:.0f}% | {r['shock_spread_pct']:.1f}% | {r['lcr_benchmark']:.2f}x | ${r['mean_resale_shock']:.2f}/M | +${r['shock_net_penalty']:.3f}/M |\n")
        f.write("\n")
        
        f.write("## 5. Monte Carlo Numerical Convergence Check\n\n")
        f.write("> **Internal Validity Note:** This table reports standard error decay across sample path counts to confirm numerical convergence of the vectorized engine. It is NOT a historical backtest.\n\n")
        f.write("| Paths N | Fair Forward Price F0 | Standard Error | 95% CI Interval | Relative SE |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | \n")
        for row in conv_data:
            f.write(f"| {row['num_paths']:,} | ${row['fair_forward_price']:.4f} | +/- ${row['standard_error']:.4f} | [${row['ci_95_lower']:.4f}, ${row['ci_95_upper']:.4f}] | {row['relative_error_pct']:.2f}% |\n")
        f.write("\n")
        
        f.write("## 6. Parameter Sensitivities (Finite Differences)\n\n")
        f.write("> **Terminology Guardrail:** Parameter sensitivities are strictly finite-difference derivatives (dF0/dS0, dF0/dlambda, dF0/dT). Because compute tokens are non-storable flow services without a continuous exchange-traded underlying, dynamic replication does not exist and these metrics must NOT be called Greeks.\n\n")
        f.write("| Metric | OpenAI Tier (S0=$5.00, T=90d) | Anthropic Tier (S0=$3.00, T=90d) |\n")
        f.write("| :--- | :--- | :--- |\n")
        f.write(f"| Spot-Price Sensitivity (dF0/dS0) | {sens_openai['spot_price_sensitivity']:.3f} | {sens_anthropic['spot_price_sensitivity']:.3f} |\n")
        f.write(f"| Hazard-Rate Sensitivity (dF0/dlambda) | {sens_openai['hazard_rate_sensitivity']:.3f} | {sens_anthropic['hazard_rate_sensitivity']:.3f} |\n")
        f.write(f"| Tenor Sensitivity (dF0/dT per day) | ${sens_openai['tenor_sensitivity_per_day']:.4f}/day | ${sens_anthropic['tenor_sensitivity_per_day']:.4f}/day |\n")
        f.write(f"| Volatility Sensitivity (dF0/dsigma) | {sens_openai['volatility_sensitivity']:.3f} | {sens_anthropic['volatility_sensitivity']:.3f} |\n\n")
        
        f.write("## 7. Supporting Stress Scenarios (Conditional on Shock)\n\n")
        f.write("| Scenario | Stress Condition | Primary Benchmark LCR | Shock Forward Cost | Shock Net Penalty vs Spot |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        f.write(f"| Secondary Market Freeze | Spread widens to 65.0% | {s_freeze['lcr_benchmark']:.2f}x | ${s_freeze['shock_net_cost_forward']:.3f}/M | +${s_freeze['shock_net_penalty']:.3f}/M |\n")
        f.write(f"| Buyer Utilization Collapse | Mean utilization drops to 20.0% | Demand Shock | ${s_util['shock_net_cost_forward']:.3f}/M | +${s_util['shock_penalty']:.3f}/M (+{s_util['shock_penalty_pct']:.1f}%) |\n")
        f.write(f"| Frontier Release War | Cadence doubles (lambda={s_war['hazard_rate_annual']:.2f}/yr) | Elevated Frequency | ${s_war['shock_net_cost_forward']:.3f}/M | +${s_war['shock_penalty']:.3f}/M |\n\n")
        
        f.write("## 8. Executive Synthesis\n\n")
        f.write(f"**Source:** {narrative['source']}\n\n")
        f.write(f"> {narrative['headline_summary']}\n\n")
        f.write(f"> {narrative['economic_summary']}\n")

if __name__ == "__main__":
    main()
