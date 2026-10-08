import re
from typing import Dict, List, Any, Set, Tuple, Optional

def extract_numbers_from_text(text: str) -> List[Tuple[float, str]]:
    results = []
    pattern = re.compile(r"(\$)?([0-9]+(?:\.[0-9]+)?)(%)?")
    for m in pattern.finditer(text):
        num_str = m.group(2)
        raw_str = m.group(0)
        val = float(num_str)
        results.append((val, raw_str))
    return results

def collect_ground_truth_numbers(data: Any) -> Set[float]:
    collected = set()
    if isinstance(data, (int, float)):
        val = float(data)
        collected.add(val)
        collected.add(round(val, 6))
        collected.add(round(val, 4))
        collected.add(round(val, 2))
        collected.add(round(val * 100.0, 2))
        collected.add(round(val * 100.0, 1))
        collected.add(float(int(val)))
    elif isinstance(data, str):
        for num, _ in extract_numbers_from_text(data):
            collected.add(num)
    elif isinstance(data, dict):
        for v in data.values():
            collected.update(collect_ground_truth_numbers(v))
    elif isinstance(data, (list, tuple)):
        for item in data:
            collected.update(collect_ground_truth_numbers(item))
    return collected

def verify_narrative_grounding(narrative: str, ground_truth: Dict[str, Any]) -> Dict[str, Any]:
    extracted = extract_numbers_from_text(narrative)
    gt_numbers = collect_ground_truth_numbers(ground_truth)

    if not extracted:
        return {
            "is_grounded": True,
            "accuracy": 1.0,
            "total_numbers": 0,
            "grounded_count": 0,
            "unverified_numbers": []
        }

    unverified = []
    grounded_count = 0

    for num, raw_str in extracted:
        matched = False
        for gt in gt_numbers:
            if abs(num - gt) < 1e-2 or (gt > 0 and abs((num - gt) / gt) <= 0.02):
                matched = True
                break
        if matched:
            grounded_count += 1
        else:
            unverified.append(raw_str)

    accuracy = grounded_count / len(extracted)
    return {
        "is_grounded": len(unverified) == 0,
        "accuracy": round(accuracy, 4),
        "total_numbers": len(extracted),
        "grounded_count": grounded_count,
        "unverified_numbers": unverified
    }

def verify_tool_grounding(narrative: str, tool_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    extracted = extract_numbers_from_text(narrative)
    if not extracted:
        return {
            "is_grounded": True,
            "accuracy": 1.0,
            "total_numbers": 0,
            "bound_tool_calls": {},
            "unverified_numbers": []
        }

    bound_calls = {}
    unverified = []
    grounded_count = 0

    for num, raw_str in extracted:
        found_tool = None
        for tr in tool_records:
            t_id = tr.get("tool_call_id", "")
            t_res = tr.get("result", {})
            t_nums = collect_ground_truth_numbers(t_res)
            for tn in t_nums:
                if abs(num - tn) < 1e-2 or (tn > 0 and abs((num - tn) / tn) <= 0.02):
                    found_tool = t_id
                    break
            if found_tool:
                break
        if found_tool:
            grounded_count += 1
            bound_calls[raw_str] = found_tool
        else:
            unverified.append(raw_str)

    accuracy = grounded_count / len(extracted)
    return {
        "is_grounded": len(unverified) == 0,
        "accuracy": round(accuracy, 4),
        "total_numbers": len(extracted),
        "bound_tool_calls": bound_calls,
        "unverified_numbers": unverified
    }

def generate_grounded_procurement_narrative(res: Dict[str, Any]) -> str:
    baseline = res["total_baseline_spend_usd"]
    parity = res["total_parity_net_spend_usd"]
    outperf = round(res["cost_outperformance_pct"] * 100.0, 2)
    ceiling = res["spend_ceiling_usd"]
    max_share = round(res["max_provider_share"] * 100.0, 2)

    narrative = (
        f"Procurement analysis completed: baseline expenditure is ${baseline:.2f} compared to "
        f"${parity:.2f} under Parity optimal reservation. This achieves an outperformance of "
        f"{outperf:.2f}% while adhering to the ${ceiling:.2f} spend ceiling. Maximum provider "
        f"allocation is constrained to {max_share:.2f}%."
    )
    return narrative
