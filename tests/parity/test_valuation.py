from pathlib import Path
import numpy as np
from parity.valuation.lsm import price_american_resale_option
from parity.valuation.shapley import compute_exact_shapley_decomposition
from parity.valuation.zopa import (
    compute_buyer_valuation,
    compute_seller_reservation_cost,
    evaluate_zopa_interval,
    evaluate_zopa_width_contraction
)
from parity.valuation.runner import run_valuation_module

def test_lsm_american_option_pricing() -> None:
    spot_paths = np.full((100, 11), 5.0)
    res = price_american_resale_option(spot_paths, tenor_days=30)
    assert res["option_value"] >= 0.0
    assert res["standard_error"] >= 0.0

def test_shapley_decomposition_properties() -> None:
    res = compute_exact_shapley_decomposition(spot_initial=5.00, tenor_days=90)
    assert res["is_efficient"] is True
    assert res["is_symmetric"] is True
    assert res["residual_efficiency"] < 1e-4

def test_zopa_interval_and_contraction() -> None:
    zopa_positive = evaluate_zopa_interval(buyer_valuation=4.50, seller_cost=3.00)
    assert zopa_positive["has_zopa"] is True
    assert zopa_positive["zopa_width"] == 1.50

    zopa_negative = evaluate_zopa_interval(buyer_valuation=2.50, seller_cost=3.00)
    assert zopa_negative["has_zopa"] is False
    assert zopa_negative["zopa_width"] == 0.0

    contraction = evaluate_zopa_width_contraction()
    assert contraction["is_monotonically_contracting"] is True

def test_module_3_valuation_runner(tmp_path: Path) -> None:
    out_file = tmp_path / "valuation_curves.json"
    res = run_valuation_module(output_path=out_file)
    assert out_file.exists()
    metrics = res["metrics"]
    assert metrics["G13_lsm_option_non_negativity"] == 1.0
    assert metrics["G14_lsm_panel_stability_se"] <= 0.02
    assert metrics["G15_early_exercise_monotonicity"] == 1.0
    assert metrics["G16_shapley_efficiency_residual"] == 1.0
    assert metrics["G17_shapley_symmetry_parity"] == 1.0
    assert metrics["G18_zopa_existence_identification_rate"] >= 0.90
    assert metrics["G19_zopa_width_contraction_monotonicity"] == 1.0
