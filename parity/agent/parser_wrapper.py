import csv
import io
import re
from typing import Dict, List, Tuple, Any, Optional

CANONICAL_COLUMNS = {
    "date": ["date", "dt", "timestamp", "day"],
    "model": ["model", "model_name", "engine"],
    "prompt_tokens": ["prompt_tokens", "input_tok", "input_tokens", "prompt_tok", "input"],
    "completion_tokens": ["completion_tokens", "output_tok", "output_tokens", "completion_tok", "output"],
    "total_tokens": ["total_tokens", "tokens", "tot_tok", "total"],
    "cost": ["cost", "amount", "spend_usd", "spend"]
}

def normalize_column_name(raw_name: str) -> Optional[str]:
    cleaned = raw_name.strip().lower()
    cleaned = re.sub(r"[_\s]+", "_", cleaned)
    for canonical, aliases in CANONICAL_COLUMNS.items():
        if cleaned == canonical or cleaned in aliases:
            return canonical
    return None

def infer_column_mapping_from_data(rows: List[List[str]]) -> Dict[int, str]:
    if not rows:
        return {}
    
    col_count = max(len(r) for r in rows)
    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    mapping = {}

    date_col = None
    model_col = None
    float_cols = []
    int_cols = []

    for c in range(col_count):
        vals = [r[c].strip() for r in rows if len(r) > c and r[c].strip()]
        if not vals:
            continue
        
        date_hits = sum(1 for v in vals if date_regex.match(v))
        if date_hits >= len(vals) * 0.4:
            date_col = c
            continue

        model_hits = sum(1 for v in vals if "/" in v or any(m in v.lower() for m in ["gpt", "claude", "gemini", "deepseek", "mistral"]))
        if model_hits >= len(vals) * 0.4:
            model_col = c
            continue

        numeric_vals = []
        for v in vals:
            try:
                numeric_vals.append(float(v))
            except ValueError:
                pass

        if len(numeric_vals) >= len(vals) * 0.4:
            has_decimals = any("." in v and not v.endswith(".0") for v in vals)
            if has_decimals or any(0.0 < num < 100.0 for num in numeric_vals):
                float_cols.append(c)
            else:
                int_cols.append(c)

    if date_col is not None:
        mapping[date_col] = "date"
    if model_col is not None:
        mapping[model_col] = "model"
    if float_cols:
        mapping[float_cols[0]] = "cost"

    if len(int_cols) == 3:
        sums_found = False
        for p_idx in int_cols:
            for c_idx in int_cols:
                if p_idx == c_idx:
                    continue
                rem_idx = [x for x in int_cols if x not in (p_idx, c_idx)][0]
                matching_sums = 0
                for r in rows:
                    try:
                        v1 = int(r[p_idx])
                        v2 = int(r[c_idx])
                        v3 = int(r[rem_idx])
                        if v1 + v2 == v3:
                            matching_sums += 1
                    except (ValueError, IndexError):
                        pass
                if matching_sums >= 3:
                    mapping[p_idx] = "prompt_tokens"
                    mapping[c_idx] = "completion_tokens"
                    mapping[rem_idx] = "total_tokens"
                    sums_found = True
                    break
            if sums_found:
                break
        if not sums_found:
            mapping[int_cols[0]] = "prompt_tokens"
            mapping[int_cols[1]] = "completion_tokens"
            mapping[int_cols[2]] = "total_tokens"
    elif len(int_cols) == 2:
        mapping[int_cols[0]] = "prompt_tokens"
        mapping[int_cols[1]] = "completion_tokens"
    elif len(int_cols) == 1:
        mapping[int_cols[0]] = "total_tokens"

    return mapping

def extract_valid_rows_with_mapping(raw_rows: List[List[str]], col_map: Dict[int, str]) -> List[Dict[str, Any]]:
    recovered = []
    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    for row in raw_rows:
        row_dict = {}
        for idx, canon in col_map.items():
            if idx < len(row):
                row_dict[canon] = row[idx].strip()

        if "date" not in row_dict or not date_regex.match(row_dict["date"]):
            continue

        try:
            p_tok = int(row_dict.get("prompt_tokens", "0"))
            c_tok = int(row_dict.get("completion_tokens", "0"))
            t_tok = int(row_dict.get("total_tokens", str(p_tok + c_tok)))
            cost_val = float(row_dict.get("cost", "0.0"))

            if p_tok < 0 or c_tok < 0 or t_tok < 0 or cost_val < 0.0:
                continue

            recovered.append({
                "date": row_dict["date"],
                "model": row_dict.get("model", ""),
                "prompt_tokens": p_tok,
                "completion_tokens": c_tok,
                "total_tokens": t_tok,
                "cost": round(cost_val, 4)
            })
        except (ValueError, TypeError):
            continue
    return recovered

def parse_corrupted_csv(csv_content: str) -> Dict[str, Any]:
    f = io.StringIO(csv_content.strip())
    reader = csv.reader(f)
    try:
        raw_headers = next(reader)
    except StopIteration:
        return {
            "success": False,
            "headers_repaired": False,
            "recovered_rows": [],
            "header_map": {}
        }

    raw_rows = list(reader)
    if len(raw_headers) == 1 and (";" in raw_headers[0] or "\t" in raw_headers[0]):
        delimiter = ";" if ";" in raw_headers[0] else "\t"
        f = io.StringIO(csv_content.strip())
        reader = csv.reader(f, delimiter=delimiter)
        raw_headers = next(reader)
        raw_rows = list(reader)

    header_map = {}
    for idx, h in enumerate(raw_headers):
        canon = normalize_column_name(h)
        if canon:
            header_map[idx] = canon

    required = {"date", "model", "prompt_tokens", "completion_tokens", "total_tokens", "cost"}
    mapped_canonicals = set(header_map.values())
    headers_repaired = len(mapped_canonicals.intersection(required)) >= 4

    recovered_rows = extract_valid_rows_with_mapping(raw_rows, header_map)

    if len(recovered_rows) < 3 and raw_rows:
        inferred_map = infer_column_mapping_from_data(raw_rows)
        if len(inferred_map) >= 4:
            inferred_rows = extract_valid_rows_with_mapping(raw_rows, inferred_map)
            if len(inferred_rows) > len(recovered_rows):
                recovered_rows = inferred_rows
                header_map = inferred_map
                headers_repaired = True

    return {
        "success": headers_repaired and len(recovered_rows) > 0,
        "headers_repaired": headers_repaired,
        "recovered_rows": recovered_rows,
        "header_map": header_map
    }

def evaluate_corruption_suite(suite: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_suites = len(suite)
    headers_repaired_count = 0
    total_valid_rows = 0
    total_recovered_rows = 0

    for item in suite:
        parsed = parse_corrupted_csv(item["csv_content"])
        if parsed["headers_repaired"]:
            headers_repaired_count += 1
        
        meta = item["metadata"]
        valid_rows = meta["valid_rows"]
        recovered = len(parsed["recovered_rows"])
        total_valid_rows += valid_rows
        total_recovered_rows += min(recovered, valid_rows)

    header_repair_rate = headers_repaired_count / max(1, total_suites)
    row_recovery_rate = total_recovered_rows / max(1, total_valid_rows)

    return {
        "header_repair_rate": round(header_repair_rate, 4),
        "row_recovery_rate": round(row_recovery_rate, 4),
        "total_suites": total_suites,
        "total_valid_rows": total_valid_rows,
        "total_recovered_rows": total_recovered_rows
    }
