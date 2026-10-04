from parity.config import (
    load_parity_config,
    load_substitutability_config,
    load_obsolescence_config,
    load_valuation_config,
    load_clearing_config,
    load_seller_config,
    load_agent_config,
    ParityConfig
)

def test_config_defaults_match() -> None:
    cfg = load_parity_config()
    assert isinstance(cfg, ParityConfig)
    assert len(cfg.substitutability.archetypes) == 8
    assert cfg.obsolescence.min_clusters == 6
    assert len(cfg.valuation.panel_cells) == 5
    assert cfg.clearing.platform_fee_bps == 25.0
    assert cfg.seller.target_utilization == 0.85
    assert cfg.agent.dev_corruption_seed == 42
    assert cfg.agent.test_corruption_seed == 1337

def test_individual_config_loaders() -> None:
    sub = load_substitutability_config()
    obs = load_obsolescence_config()
    val = load_valuation_config()
    clr = load_clearing_config()
    sel = load_seller_config()
    agt = load_agent_config()

    assert sub.decision_threshold == 0.95
    assert obs.bootstrap_samples == 1000
    assert val.discount_rate == 0.04
    assert clr.welfare_ratio_gate_min == 0.85
    assert sel.cannibalization_dampener == 0.80
    assert agt.sub_cap_ceiling_check_usd == 4.00
