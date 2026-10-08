from stampede.stages.parity_live import run_live_sequential_parity

def test_sequential_parity_matches_expected_decision():
    outcomes_cand = [True] * 40
    outcomes_inc = [True] * 40
    res = run_live_sequential_parity(
        incumbent_outcomes=outcomes_inc,
        candidate_outcomes=outcomes_cand,
        theta_0=0.90
    )
    assert res.decision == "parity"
    assert res.posterior_mean.value > 0.90

def test_sequential_inferiority_detected():
    outcomes_cand = [False] * 30
    outcomes_inc = [True] * 30
    res = run_live_sequential_parity(
        incumbent_outcomes=outcomes_inc,
        candidate_outcomes=outcomes_cand,
        theta_0=0.90
    )
    assert res.decision == "inferior"
    assert res.posterior_mean.value < 0.50
