from stampede.stages.judge_adjust import adjust_judge_rate

def test_judge_adjustment_recovers_true_rate():
    res = adjust_judge_rate(
        apparent_rate=0.85,
        n_evals=100,
        sensitivity=0.95,
        specificity=0.90
    )
    assert 0.0 <= res.adjusted_theta_mean.value <= 1.0
    assert res.youden_index.value > 0.5
    assert not res.blocks_parity_decision

def test_judge_adjustment_blocks_low_youden():
    res = adjust_judge_rate(
        apparent_rate=0.70,
        n_evals=50,
        sensitivity=0.60,
        specificity=0.60
    )
    assert res.youden_index.value < 0.5
    assert res.blocks_parity_decision
