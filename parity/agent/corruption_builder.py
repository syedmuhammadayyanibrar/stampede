import csv
import io
import random
from typing import Dict, List, Tuple, Any

def generate_clean_usage_rows(num_rows: int = 30, seed: int = 42) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    rows = []
    base_date = 1722470400
    for i in range(num_rows):
        day_offset = i * 86400
        d_str = f"2026-08-{i%28 + 1:02d}"
        in_tok = rng.randint(500000, 2000000)
        out_tok = rng.randint(200000, 800000)
        tot_tok = in_tok + out_tok
        model = "anthropic/claude-3.5-sonnet" if i % 2 == 0 else "openai/gpt-4o"
        rows.append({
            "date": d_str,
            "model": model,
            "prompt_tokens": in_tok,
            "completion_tokens": out_tok,
            "total_tokens": tot_tok,
            "cost": round(tot_tok * 0.000003, 4)
        })
    return rows

def corrupt_csv(
    rows: List[Dict[str, Any]],
    seed: int,
    header_corruption_type: str = "noisy_casing_and_spaces",
    corrupt_row_fraction: float = 0.20
) -> Tuple[str, Dict[str, Any]]:
    rng = random.Random(seed)
    
    header_variants = {
        "noisy_casing_and_spaces": [" Date ", "MODEL_NAME", " Prompt Tokens ", " completion_Tokens ", "Total_Tokens", "spend_usd "],
        "transposed_cols": ["total_tokens", "date", "model", "prompt_tokens", "completion_tokens", "cost"],
        "abbreviated_headers": ["dt", "engine", "input_tok", "output_tok", "tokens", "amount"],
        "mixed_delimiters": ["Date;Model;Input;Output;Total;Cost"]
    }
    
    chosen_headers = header_variants.get(header_corruption_type, list(rows[0].keys()))
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(chosen_headers)
    
    valid_row_count = 0
    corrupted_row_count = 0

    for r in rows:
        roll = rng.random()
        if roll < corrupt_row_fraction:
            corrupted_row_count += 1
            corr_choice = rng.randint(0, 3)
            if corr_choice == 0:
                row_vals = ["NOT_A_DATE", r["model"], str(r["prompt_tokens"]), str(r["completion_tokens"]), str(r["total_tokens"]), str(r["cost"])]
            elif corr_choice == 1:
                row_vals = [r["date"], r["model"], "-500", "-200", "-700", str(r["cost"])]
            elif corr_choice == 2:
                row_vals = [r["date"], r["model"], "NULL", "INVALID", "NaN", "0.0"]
            else:
                row_vals = [r["date"], r["model"]]
        else:
            valid_row_count += 1
            row_vals = [
                r["date"],
                r["model"],
                str(r["prompt_tokens"]),
                str(r["completion_tokens"]),
                str(r["total_tokens"]),
                str(r["cost"])
            ]
        writer.writerow(row_vals)

    meta = {
        "seed": seed,
        "header_type": header_corruption_type,
        "total_rows": len(rows),
        "valid_rows": valid_row_count,
        "corrupted_rows": corrupted_row_count
    }
    return output.getvalue(), meta

def generate_corruption_suite(seed: int) -> List[Dict[str, Any]]:
    suite = []
    header_types = [
        "noisy_casing_and_spaces",
        "transposed_cols",
        "abbreviated_headers"
    ]
    for idx, ht in enumerate(header_types):
        clean_rows = generate_clean_usage_rows(num_rows=25, seed=seed + idx * 10)
        csv_str, meta = corrupt_csv(clean_rows, seed=seed + idx * 10, header_corruption_type=ht, corrupt_row_fraction=0.15)
        suite.append({
            "test_id": f"corruption_{seed}_{ht}",
            "csv_content": csv_str,
            "metadata": meta
        })
    return suite
