from pathlib import Path
from parity.clearing.auction import AuctionBid, AuctionAsk, clear_resale_market
from parity.clearing.runner import generate_synthetic_auction_orderbook, run_clearing_module

def test_auction_clearing_mechanics() -> None:
    bids = [
        AuctionBid("b1", "buyer1", "code_generation", "openai/gpt-4o", 5.0, 10.0),
        AuctionBid("b2", "buyer2", "code_generation", "openai/gpt-4o", 4.0, 10.0)
    ]
    asks = [
        AuctionAsk("a1", "seller1", "openai/gpt-4o", 3.0, 15.0)
    ]
    matrix = {}
    res = clear_resale_market(bids, asks, matrix, use_substitutability=False)
    assert res["num_matches"] == 2
    assert res["traded_volume_m"] == 15.0
    assert res["total_welfare"] > 0.0

def test_substitutability_uplifts_welfare() -> None:
    bids = [
        AuctionBid("b1", "buyer1", "structured_extraction", "openai/gpt-4o", 4.5, 20.0)
    ]
    asks = [
        AuctionAsk("a1", "seller1", "deepseek/deepseek-chat", 1.5, 20.0)
    ]
    matrix = {
        "structured_extraction": {
            "deepseek/deepseek-chat": {"decision": "NON_INFERIOR", "p_non_inferior": 0.96}
        }
    }
    res_iso = clear_resale_market(bids, asks, matrix, use_substitutability=False)
    assert res_iso["num_matches"] == 0

    res_sub = clear_resale_market(bids, asks, matrix, use_substitutability=True)
    assert res_sub["num_matches"] == 1
    assert res_sub["total_welfare"] > 0.0

def test_module_4_clearing_runner(tmp_path: Path) -> None:
    out_file = tmp_path / "clearing_results.json"
    res = run_clearing_module(output_path=out_file)
    assert out_file.exists()
    metrics = res["metrics"]
    assert metrics["G20_clearing_envy_freeness_rate"] >= 0.95
    assert metrics["G21_market_welfare_uplift_ratio"] >= 1.08
