from eval import verify_thresholds_lock, main

def test_thresholds_lock_valid() -> None:
    assert verify_thresholds_lock() is True

def test_evaluation_runner_30_gates_pass() -> None:
    exit_code = main()
    assert exit_code == 0
