from pathlib import Path
from typing import Dict, List, Any
import numpy as np
from parity.config import load_valuation_config
from parity.obsolescence.price_path import simulate_jump_diffusion_paths
from parity.valuation.lsm import price_american_resale_option
from parity.valuation.shapley import compute_exact_shapley_decomposition
from parity.valuation.zopa import (
    evaluate_zopa_interval,
    evaluate_zopa_width_contraction,
    compute_buyer_valuation
)
from parity.io import write_json_atomic

def run_valuation_module(
    output_path: Path = Path("data/parity/valuation_curves.json"),
    random_seed: int = 42
) -> Dict[str, Any]:
    cfg = load_valuation_config()
    panel = cfg.panel_cells
    replications = cfg.panel_replications

    panel_results = []
    max_se = 0.0
    all_non_negative = True
    all_boundary_monotonic = True

    for cell in panel:
        cell_option_vals = []
        for rep in range(replications):
            rep_seed = random_seed + (hash(cell.cell_id) % 10000) + rep * 101
            paths, terminal, _ = simulate_jump_diffusion_paths(
                spot_initial=5.00,
                drift=-0.25,
                volatility=0.22,
                hazard_rate=1.2 if cell.successor_active else 0.5,
                jump_mean=0.40,
                tenor_days=cell.tenor_days,
                num_paths=1000,
                seed=rep_seed
            )
            resale_spread = max(0.02, 0.06 - (cell.conversion_rate * 0.03))
            lsm_res = price_american_resale_option(
                spot_paths=paths,
                resale_spread=resale_spread,
                discount_rate=cfg.discount_rate,
                tenor_days=cell.tenor_days,
                utilization=0.75,
                degree=cfg.basis_polynomial_degree
            )
            v = lsm_res["option_value"]
            if v < 0.0:
                all_non_negative = False
            cell_option_vals.append(v)
            if not lsm_res["is_boundary_monotonic"]:
                all_boundary_monotonic = False

        cell_se = float(np.std(cell_option_vals, ddof=1) / np.sqrt(replications))
        if cell_se > max_se:
            max_se = cell_se

        panel_results.append({
            "cell_id": cell.cell_id,
            "tenor_days": cell.tenor_days,
            "mean_option_value": round(float(np.mean(cell_option_vals)), 4),
            "standard_error": round(cell_se, 6)
        })

    shapley_res = compute_exact_shapley_decomposition(
        spot_initial=5.00,
        drift=-0.35,
        volatility=0.28,
        hazard_rate=1.85,
        jump_mean=0.45,
        spread=0.06,
        tenor_days=90
    )

    zopa_check = evaluate_zopa_width_contraction()

    zopa_cases = [
        (4.50, 2.50),
        (3.80, 2.80),
        (3.20, 2.10),
        (4.10, 3.00),
        (3.50, 2.40),
        (3.90, 2.90),
        (4.00, 3.10),
        (4.30, 2.60),
        (3.60, 2.70),
        (3.70, 2.50)
    ]
    zopa_found_count = sum(1 for v, c in zopa_cases if evaluate_zopa_interval(v, c)["has_zopa"])
    zopa_id_rate = zopa_found_count / len(zopa_cases)

    metrics = {
        "G13_lsm_option_non_negativity": 1.0 if all_non_negative else 0.0,
        "G14_lsm_panel_stability_se": round(max_se, 6),
        "G15_early_exercise_monotonicity": 1.0 if all_boundary_monotonic else 0.0,
        "G16_shapley_efficiency_residual": 1.0 if shapley_res["is_efficient"] else 0.0,
        "G17_shapley_symmetry_parity": 1.0 if shapley_res["is_symmetric"] else 0.0,
        "G18_zopa_existence_identification_rate": round(zopa_id_rate, 4),
        "G19_zopa_width_contraction_monotonicity": 1.0 if zopa_check["is_monotonically_contracting"] else 0.0
    }

    payload = {
        "metrics": metrics,
        "panel_results": panel_results,
        "shapley": shapley_res,
        "zopa": zopa_check
    }
    write_json_atomic(output_path, payload)
    return payload
