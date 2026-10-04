from pathlib import Path
from typing import Dict, List, Any
from parity.seller.capacity import evaluate_spread_compression
from parity.io import read_yaml, write_json_atomic

def run_seller_module(
    config_path: Path = Path("config/seller.yaml"),
    output_path: Path = Path("data/parity/seller_curves.json")
) -> Dict[str, Any]:
    cannibalization = 0.80
    if config_path.exists():
        cfg = read_yaml(config_path)
        cannibalization = cfg.get("cannibalization_dampener", 0.80)

    results = evaluate_spread_compression(
        primary_price=4.0,
        baseline_utilization=0.65,
        cannibalization_dampener=cannibalization
    )

    metrics = {
        "G22_secondary_spread_compression_50pct": results["spread_compression_ratio"],
        "baseline_spread_usd": results["baseline_spread"],
        "spread_at_50pct_uptake_usd": results["spread_at_50pct"],
        "compression_pct": round(results["spread_compression_ratio"] * 100.0, 2),
        "baseline_utilization": results["baseline_utilization"],
        "utilization_at_50pct": results["utilization_at_50pct"]
    }

    payload = {
        "metrics": metrics,
        "curves": {
            "uptake_grid": results["uptake_grid"],
            "spreads": results["spreads"],
            "utilizations": results["utilizations"]
        }
    }

    write_json_atomic(output_path, payload)
    return payload
