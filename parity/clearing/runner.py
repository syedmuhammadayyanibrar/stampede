from pathlib import Path
from typing import Dict, List, Any
import numpy as np
from parity.clearing.auction import AuctionBid, AuctionAsk, clear_resale_market
from parity.io import read_json, write_json_atomic

def generate_synthetic_auction_orderbook(
    seed: int = 42
) -> tuple[List[AuctionBid], List[AuctionAsk]]:
    rng = np.random.default_rng(seed)
    archetypes = [
        "code_generation",
        "structured_extraction",
        "summarization",
        "creative_writing",
        "reasoning_math",
        "rag_qa",
        "classification",
        "translation"
    ]
    models = [
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "anthropic/claude-3.5-sonnet",
        "deepseek/deepseek-chat",
        "google/gemini-2.0-flash-001"
    ]

    bids = []
    for i in range(25):
        arch = archetypes[i % len(archetypes)]
        incumbent = "openai/gpt-4o"
        max_p = float(rng.uniform(3.50, 5.20))
        qty = float(rng.uniform(10.0, 50.0))
        bids.append(AuctionBid(
            bid_id=f"bid_{i+1:03d}",
            buyer_id=f"buyer_{i % 8 + 1:02d}",
            archetype=arch,
            incumbent_model=incumbent,
            max_price_per_m=round(max_p, 2),
            quantity_m=round(qty, 1)
        ))

    asks = []
    for j in range(25):
        offered = models[j % len(models)]
        base_cost = 2.50 if "gpt-4o" in offered else 1.20
        min_p = float(rng.uniform(base_cost * 0.8, base_cost * 1.3))
        qty = float(rng.uniform(15.0, 60.0))
        asks.append(AuctionAsk(
            ask_id=f"ask_{j+1:03d}",
            seller_id=f"seller_{j % 5 + 1:02d}",
            model_offered=offered,
            min_price_per_m=round(min_p, 2),
            quantity_m=round(qty, 1)
        ))

    return bids, asks

def run_clearing_module(
    matrix_path: Path = Path("data/parity/substitutability_matrix.json"),
    output_path: Path = Path("data/parity/clearing_results.json"),
    seed: int = 42
) -> Dict[str, Any]:
    matrix_data = read_json(matrix_path)
    sub_matrix = matrix_data.get("matrix", {})

    bids, asks = generate_synthetic_auction_orderbook(seed=seed)

    isolated_res = clear_resale_market(
        bids=bids,
        asks=asks,
        substitutability_matrix=sub_matrix,
        use_substitutability=False
    )

    substitutability_res = clear_resale_market(
        bids=bids,
        asks=asks,
        substitutability_matrix=sub_matrix,
        use_substitutability=True
    )

    w_iso = max(1.0, isolated_res["total_welfare"])
    w_sub = substitutability_res["total_welfare"]
    welfare_ratio = float(w_sub / w_iso)

    envy_free_rate = substitutability_res["envy_free_rate"]

    metrics = {
        "G20_clearing_envy_freeness_rate": round(envy_free_rate, 4),
        "G21_market_welfare_uplift_ratio": round(welfare_ratio, 4),
        "isolated_welfare_usd": round(w_iso, 2),
        "substitutability_welfare_usd": round(w_sub, 2),
        "welfare_uplift_pct": round((welfare_ratio - 1.0) * 100.0, 2)
    }

    payload = {
        "metrics": metrics,
        "isolated_clearing": {
            "total_welfare": isolated_res["total_welfare"],
            "traded_volume_m": isolated_res["traded_volume_m"],
            "num_matches": isolated_res["num_matches"]
        },
        "substitutability_clearing": {
            "total_welfare": substitutability_res["total_welfare"],
            "traded_volume_m": substitutability_res["traded_volume_m"],
            "num_matches": substitutability_res["num_matches"]
        }
    }
    write_json_atomic(output_path, payload)
    return payload
