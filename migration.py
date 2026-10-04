import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import numpy as np
from data_sources.openrouter import fetch_rankings_daily

def load_launch_events(path: str = "data/launch_events.json") -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def analyze_event_migration(event: Dict[str, Any]) -> Dict[str, Any]:
    t0 = datetime.strptime(event["launch_date"], "%Y-%m-%d")
    s_date = (t0 - timedelta(days=14)).strftime("%Y-%m-%d")
    e_date = (t0 + timedelta(days=28)).strftime("%Y-%m-%d")
    
    rows = fetch_rankings_daily(s_date, e_date)
    
    by_date: Dict[str, Dict[str, int]] = {}
    for r in rows:
        d = r["date"]
        by_date.setdefault(d, {})[r["model_permaslug"]] = int(r["total_tokens"])
    
    dates = sorted(by_date.keys())
    timeline = []
    pre_shares = []
    
    old_slug = event["old_model_slug"]
    new_slug = event["new_model_slug"]
    
    for d_str in dates:
        d_obj = datetime.strptime(d_str, "%Y-%m-%d")
        rel_days = (d_obj - t0).days
        day_models = by_date[d_str]
        tot = sum(day_models.values())
        
        old_tok = day_models.get(old_slug, 0)
        new_tok = day_models.get(new_slug, 0)
        
        old_sh = (old_tok / tot) if tot > 0 else 0.0
        new_sh = (new_tok / tot) if tot > 0 else 0.0
        
        if rel_days < 0:
            pre_shares.append(old_sh)
            
        timeline.append({
            "date": d_str,
            "rel_day": rel_days,
            "old_tokens": old_tok,
            "new_tokens": new_tok,
            "old_share": round(old_sh, 5),
            "new_share": round(new_sh, 5),
            "total_tokens": tot
        })
    
    s_pre = float(np.mean(pre_shares)) if pre_shares else 0.001
    
    def get_window_phi(target_day: int, window_radius: int = 2) -> float:
        matches = [t["old_share"] for t in timeline if abs(t["rel_day"] - target_day) <= window_radius]
        if not matches or s_pre <= 1e-6:
            return 0.50
        s_post = float(np.mean(matches))
        return float(np.clip(1.0 - (s_post / s_pre), 0.0, 1.0))
    
    phi_7 = get_window_phi(7)
    phi_14 = get_window_phi(14)
    phi_21 = get_window_phi(21)
    phi_28 = get_window_phi(28)
    
    return {
        "id": event["id"],
        "provider": event["provider"],
        "old_model": old_slug,
        "new_model": new_slug,
        "launch_date": event["launch_date"],
        "pre_launch_share": round(s_pre, 4),
        "phi_7": round(phi_7, 4),
        "phi_14": round(phi_14, 4),
        "phi_21": round(phi_21, 4),
        "phi_28": round(phi_28, 4),
        "timeline": timeline
    }

def get_empirical_migration_dataset() -> Dict[str, Any]:
    events = load_launch_events()
    analyzed = []
    phi_14_list = []
    
    for ev in events:
        res = analyze_event_migration(ev)
        analyzed.append(res)
        phi_14_list.append(res["phi_14"])
    
    arr = np.array(phi_14_list)
    mean_phi = float(np.mean(arr))
    std_phi = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.05
    
    rng = np.random.default_rng(42)
    boot_means = [float(np.mean(rng.choice(arr, size=len(arr), replace=True))) for _ in range(2000)]
    ci_low = float(np.percentile(boot_means, 2.5))
    ci_high = float(np.percentile(boot_means, 97.5))
    
    return {
        "events": analyzed,
        "phi_14_samples": phi_14_list,
        "mean_switch_share": round(mean_phi, 4),
        "std_switch_share": round(std_phi, 4),
        "ci_95": [round(ci_low, 4), round(ci_high, 4)],
        "source_attribution": "Source: OpenRouter (openrouter.ai/rankings), as of 2026-10"
    }

if __name__ == "__main__":
    dataset = get_empirical_migration_dataset()
    print("EMPIRICAL LAUNCH EVENTS ANALYZED:")
    for ev in dataset["events"]:
        print(f"  [{ev['id']}] {ev['launch_date']} {ev['provider']}: Pre={ev['pre_launch_share']:.1%}, phi_14={ev['phi_14']:.1%}, phi_28={ev['phi_28']:.1%}")
    print(f"\nMean Empirical Switch Share (14d): {dataset['mean_switch_share']:.1%} (95% CI: [{dataset['ci_95'][0]:.1%}, {dataset['ci_95'][1]:.1%}])")
