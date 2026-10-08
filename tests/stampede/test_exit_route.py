from stampede.stages.exit_route import evaluate_exit_recovery, simulate_exit_recovery
from stampede.types import StandingNotices

def test_exit_route_feasible_paired_draws():
    rep = evaluate_exit_recovery(
        contract_notional_m=50.0,
        unit_strike_usd=4.00,
        tenor_days=90,
        sell_day=30,
        remaining_share=0.67,
        depth="normal",
        substitutability_feasible=True,
        n_draws=100,
        seed=42
    )

    assert rep.substitution_aware.p50_recovery_usd.value >= rep.same_model.p50_recovery_usd.value
    assert rep.secondary_spread_recovery_lift_usd.value >= 0.0
    assert rep.secondary_spread_recovery_lift_usd.lo90 is not None
    assert rep.secondary_spread_recovery_lift_usd.hi90 is not None
    assert rep.secondary_spread_recovery_lift_usd.lo90 >= 0.0
    assert rep.secondary_spread_recovery_lift_usd.hi90 >= rep.secondary_spread_recovery_lift_usd.lo90
    assert StandingNotices.SIMULATED_EXIT_POOL in rep.notices

def test_exit_route_infeasible_exact_equality():
    rep = evaluate_exit_recovery(
        contract_notional_m=50.0,
        unit_strike_usd=4.00,
        tenor_days=90,
        sell_day=30,
        remaining_share=0.67,
        depth="normal",
        substitutability_feasible=False,
        n_draws=100,
        seed=42
    )

    assert rep.substitution_aware.p10_recovery_usd.value == rep.same_model.p10_recovery_usd.value
    assert rep.substitution_aware.p50_recovery_usd.value == rep.same_model.p50_recovery_usd.value
    assert rep.substitution_aware.p90_recovery_usd.value == rep.same_model.p90_recovery_usd.value
    assert rep.secondary_spread_recovery_lift_usd.value == 0.0
    assert rep.secondary_spread_recovery_lift_usd.lo90 == 0.0
    assert rep.secondary_spread_recovery_lift_usd.hi90 == 0.0
    assert StandingNotices.SIMULATED_EXIT_POOL in rep.notices

def test_simulate_exit_recovery_helper():
    rep = simulate_exit_recovery(
        spot_at_sale=4.20,
        strike=3.50,
        remaining_days=45,
        tenor_days=90,
        substitutability_feasible=True
    )
    assert rep.recovery_substitute.value >= rep.recovery_same_model.value
    assert StandingNotices.SIMULATED_EXIT_POOL in rep.notices
