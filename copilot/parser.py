import io
import csv
import re
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import numpy as np

@dataclass
class UsageSummary:
    success: bool
    error: Optional[str]
    dates: List[str]
    daily_tokens_millions: List[float]
    total_tokens_millions: float
    mean_daily_tokens_millions: float
    std_daily_tokens_millions: float
    detected_model: str
    num_days: int

def parse_usage_csv(csv_content: str) -> UsageSummary:
    if not csv_content or not csv_content.strip():
        return UsageSummary(False, "Empty CSV content provided", [], [], 0.0, 0.0, 0.0, "unknown", 0)
    
    reader = csv.reader(io.StringIO(csv_content.strip()))
    try:
        header = [h.strip().lower() for h in next(reader)]
    except StopIteration:
        return UsageSummary(False, "No header row found", [], [], 0.0, 0.0, 0.0, "unknown", 0)
    
    date_col = -1
    model_col = -1
    in_col = -1
    out_col = -1
    tot_col = -1
    cost_col = -1
    
    for idx, col in enumerate(header):
        if col in ("date", "timestamp", "day", "created_at", "time", "usage_date"):
            date_col = idx
        elif col in ("model", "model_name", "engine", "model_permaslug"):
            model_col = idx
        elif col in ("prompt_tokens", "input_tokens", "context_tokens", "prompt"):
            in_col = idx
        elif col in ("completion_tokens", "output_tokens", "generated_tokens", "completion"):
            out_col = idx
        elif col in ("total_tokens", "tokens", "num_tokens"):
            tot_col = idx
        elif col in ("cost", "total_cost", "spend", "usd", "amount"):
            cost_col = idx
            
    if date_col == -1:
        return UsageSummary(False, "Could not identify date column in header", [], [], 0.0, 0.0, 0.0, "unknown", 0)
    
    if in_col == -1 and tot_col == -1:
        return UsageSummary(False, "Could not identify token count column in header", [], [], 0.0, 0.0, 0.0, "unknown", 0)
    
    daily_agg: Dict[str, float] = {}
    detected_models: Dict[str, int] = {}
    
    for row_idx, row in enumerate(reader):
        if not row or len(row) <= date_col:
            continue
        raw_date = row[date_col].strip()
        if not raw_date:
            continue
            
        parsed_date = None
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                parsed_date = datetime.strptime(raw_date.split("T")[0].split(" ")[0], fmt.split("T")[0].split(" ")[0]).strftime("%Y-%m-%d")
                break
            except Exception:
                pass
                
        if not parsed_date:
            continue
            
        model_name = row[model_col].strip() if model_col != -1 and len(row) > model_col else "frontier_standard"
        detected_models[model_name] = detected_models.get(model_name, 0) + 1
        
        tokens = 0.0
        try:
            if in_col != -1 and out_col != -1 and len(row) > max(in_col, out_col):
                tin = float(re.sub(r"[^\d.]", "", row[in_col]) or 0)
                tout = float(re.sub(r"[^\d.]", "", row[out_col]) or 0)
                tokens = tin + tout
            elif tot_col != -1 and len(row) > tot_col:
                tokens = float(re.sub(r"[^\d.]", "", row[tot_col]) or 0)
            elif in_col != -1 and len(row) > in_col:
                tokens = float(re.sub(r"[^\d.]", "", row[in_col]) or 0) * 1.33
        except Exception:
            tokens = 0.0
            
        if tokens < 0.0:
            continue
            
        daily_agg[parsed_date] = daily_agg.get(parsed_date, 0.0) + (tokens / 1_000_000.0)
        
    if not daily_agg:
        return UsageSummary(False, "No valid token usage rows could be extracted", [], [], 0.0, 0.0, 0.0, "unknown", 0)
        
    dates_sorted = sorted(daily_agg.keys())
    tokens_series = [daily_agg[d] for d in dates_sorted]
    
    top_model = sorted(detected_models.items(), key=lambda x: x[1], reverse=True)[0][0] if detected_models else "frontier_standard"
    total_m = float(sum(tokens_series))
    mean_m = float(np.mean(tokens_series))
    std_m = float(np.std(tokens_series, ddof=1)) if len(tokens_series) > 1 else 0.05 * mean_m
    
    return UsageSummary(
        success=True,
        error=None,
        dates=dates_sorted,
        daily_tokens_millions=[round(x, 4) for x in tokens_series],
        total_tokens_millions=round(total_m, 2),
        mean_daily_tokens_millions=round(mean_m, 4),
        std_daily_tokens_millions=round(std_m, 4),
        detected_model=top_model,
        num_days=len(dates_sorted)
    )
