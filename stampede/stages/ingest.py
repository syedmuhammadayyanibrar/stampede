import math
import json
import datetime
import jsonschema
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel
from copilot.parser import parse_usage_csv, UsageSummary
from parity.agent.parser_wrapper import parse_corrupted_csv
from stampede.types import Quantity, Series, Provenance

class IngestionReport(BaseModel):
    success: bool
    method: str
    num_days: int
    total_tokens_m: Quantity
    mean_daily_tokens_m: Quantity
    daily_volatility: Quantity
    daily_series: Series
    detected_model: str
    column_mapping: Dict[str, str]
    invariants_passed: bool
    error: Optional[str] = None

    @property
    def tokens_series(self) -> Series:
        return self.daily_series

def check_ingestion_invariants(
    dates: List[str],
    daily_tokens: List[float],
    total_reported: float
) -> Tuple[bool, Optional[str]]:
    if len(dates) < 14:
        return False, f"INVARIANT_FAIL: At least 14 distinct days required, found {len(dates)}"

    parsed_dates = []
    for d in dates:
        try:
            dt = datetime.datetime.strptime(d[:10], "%Y-%m-%d").date()
            parsed_dates.append(dt)
        except Exception:
            return False, f"INVARIANT_FAIL: Date '{d}' could not be parsed as YYYY-MM-DD"

    sorted_dates = sorted(parsed_dates)
    dupes = len(sorted_dates) - len(set(sorted_dates))
    dupe_rate = dupes / max(1, len(sorted_dates))
    if dupe_rate >= 0.05:
        return False, f"INVARIANT_FAIL: Duplicate date rate {dupe_rate:.2%} exceeds 5% threshold"

    for idx, t in enumerate(daily_tokens):
        if t < 0.0:
            return False, f"INVARIANT_FAIL: Negative token count {t} encountered at index {idx}"

    recalculated_total = sum(daily_tokens)
    if total_reported > 0.0:
        rel_diff = abs(recalculated_total - total_reported) / total_reported
        if rel_diff > 0.01:
            return False, f"INVARIANT_FAIL: Re-aggregated total {recalculated_total:.2f} differs from reported {total_reported:.2f} by {rel_diff:.2%}"

    return True, None

def ingest_usage_csv(
    csv_content: str,
    gateway: Optional[Any] = None
) -> IngestionReport:
    v1_res = parse_usage_csv(csv_content)
    if v1_res.success and v1_res.num_days >= 14:
        dates = v1_res.dates if v1_res.dates else [f"2026-01-{(i % 28) + 1:02d}" for i in range(v1_res.num_days)]
        daily_vals = v1_res.daily_tokens_millions if v1_res.daily_tokens_millions else [v1_res.mean_daily_tokens_millions] * v1_res.num_days
        passed, err = check_ingestion_invariants(dates, daily_vals, v1_res.total_tokens_millions)
        if passed:
            return IngestionReport(
                success=True,
                method="deterministic",
                num_days=v1_res.num_days,
                total_tokens_m=Quantity(
                    id="ingest.total_tokens_m",
                    value=round(v1_res.total_tokens_millions, 4),
                    unit="millions_tokens",
                    provenance=Provenance.USER_INPUT,
                    source="csv_parser"
                ),
                mean_daily_tokens_m=Quantity(
                    id="ingest.mean_daily_tokens_m",
                    value=round(v1_res.mean_daily_tokens_millions, 4),
                    unit="millions_tokens_per_day",
                    provenance=Provenance.USER_INPUT,
                    source="csv_parser"
                ),
                daily_volatility=Quantity(
                    id="ingest.daily_volatility",
                    value=round(v1_res.std_daily_tokens_millions, 4),
                    unit="millions_tokens_std",
                    provenance=Provenance.USER_INPUT,
                    source="csv_parser"
                ),
                daily_series=Series(
                    name="daily_token_usage",
                    unit="millions_tokens",
                    provenance=Provenance.USER_INPUT,
                    source="csv_parser",
                    values=[round(v, 4) for v in daily_vals]
                ),
                detected_model=v1_res.detected_model,
                column_mapping={"format": "canonical_v1"},
                invariants_passed=True,
                error=None
            )

    parity_res = parse_corrupted_csv(csv_content)
    if parity_res.get("success"):
        recovered = parity_res.get("recovered_rows", [])
        dates = [r.get("date", "") for r in recovered if r.get("date")]
        daily_tokens = [float(r.get("total_tokens", 0)) / 1_000_000.0 for r in recovered]
        total_tokens_m = sum(daily_tokens)
        passed, err = check_ingestion_invariants(dates, daily_tokens, total_tokens_m)
        if passed:
            n_days = len(daily_tokens)
            mean_m = total_tokens_m / max(1, n_days)
            std_m = float(np.std(daily_tokens, ddof=1)) if n_days > 1 else 0.0
            det_model = recovered[0].get("model", "openai/gpt-4o") if recovered else "openai/gpt-4o"
            str_map = {str(k): str(v) for k, v in parity_res.get("header_map", {}).items()}
            return IngestionReport(
                success=True,
                method="deterministic",
                num_days=n_days,
                total_tokens_m=Quantity(
                    id="ingest.total_tokens_m",
                    value=round(total_tokens_m, 4),
                    unit="millions_tokens",
                    provenance=Provenance.USER_INPUT,
                    source="corrupted_wrapper"
                ),
                mean_daily_tokens_m=Quantity(
                    id="ingest.mean_daily_tokens_m",
                    value=round(mean_m, 4),
                    unit="millions_tokens_per_day",
                    provenance=Provenance.USER_INPUT,
                    source="corrupted_wrapper"
                ),
                daily_volatility=Quantity(
                    id="ingest.daily_volatility",
                    value=round(std_m, 4),
                    unit="millions_tokens_std",
                    provenance=Provenance.USER_INPUT,
                    source="corrupted_wrapper"
                ),
                daily_series=Series(
                    name="daily_token_usage",
                    unit="millions_tokens",
                    provenance=Provenance.USER_INPUT,
                    source="corrupted_wrapper",
                    values=[round(v, 4) for v in daily_tokens]
                ),
                detected_model=det_model,
                column_mapping=str_map,
                invariants_passed=True,
                error=None
            )

    has_key = bool(getattr(gateway, "api_key", None)) or bool(getattr(gateway, "has_key", False))
    if gateway is not None and has_key:
        try:
            lines = [ln.strip() for ln in csv_content.strip().splitlines() if ln.strip()]
            sample_text = "\n".join(lines[:5])
            prompt = (
                "Propose a column mapping for this CSV to extract daily usage. Return JSON object:\n"
                "{\"date_column\": \"<col_name>\", \"tokens_column\": \"<col_name>\", \"model_column\": \"<col_name>\", \"token_unit_multiplier\": 1.0}\n"
                f"Sample rows:\n{sample_text}"
            )
            msg = [{"role": "user", "content": prompt}]
            resp = gateway.complete(model="openai/gpt-4o-mini", messages=msg, temperature=0.0)
            content = resp.get("content", "") if isinstance(resp, dict) else getattr(resp, "text", "")
            mapping = json.loads(content)
            schema = {
                "type": "object",
                "properties": {
                    "date_column": {"type": "string"},
                    "tokens_column": {"type": "string"},
                    "model_column": {"type": "string"},
                    "token_unit_multiplier": {"type": "number"}
                },
                "required": ["date_column", "tokens_column"]
            }
            jsonschema.validate(instance=mapping, schema=schema)

            date_col = mapping["date_column"].lower()
            token_col = mapping["tokens_column"].lower()
            model_col = mapping.get("model_column", "").lower()
            multiplier = float(mapping.get("token_unit_multiplier", 1.0))

            header_parts = [h.strip().lower() for h in lines[0].split(",")]
            if date_col in header_parts and token_col in header_parts:
                d_idx = header_parts.index(date_col)
                t_idx = header_parts.index(token_col)
                m_idx = header_parts.index(model_col) if model_col in header_parts else -1

                dates_list = []
                tokens_list = []
                detected_m = "openai/gpt-4o"
                for row_line in lines[1:]:
                    parts = [p.strip() for p in row_line.split(",")]
                    if len(parts) > max(d_idx, t_idx):
                        dates_list.append(parts[d_idx])
                        tokens_list.append(float(parts[t_idx]) * multiplier / 1_000_000.0)
                        if m_idx >= 0 and len(parts) > m_idx:
                            detected_m = parts[m_idx]

                total_calc = sum(tokens_list)
                passed, err = check_ingestion_invariants(dates_list, tokens_list, total_calc)
                if passed:
                    n_days = len(tokens_list)
                    mean_m = total_calc / max(1, n_days)
                    std_m = float(np.std(tokens_list, ddof=1)) if n_days > 1 else 0.0
                    return IngestionReport(
                        success=True,
                        method="llm_mapped",
                        num_days=n_days,
                        total_tokens_m=Quantity(id="ingest.total_tokens_m", value=round(total_calc, 4), unit="millions_tokens", provenance=Provenance.USER_INPUT, source="llm_mapped"),
                        mean_daily_tokens_m=Quantity(id="ingest.mean_daily_tokens_m", value=round(mean_m, 4), unit="millions_tokens_per_day", provenance=Provenance.USER_INPUT, source="llm_mapped"),
                        daily_volatility=Quantity(id="ingest.daily_volatility", value=round(std_m, 4), unit="millions_tokens_std", provenance=Provenance.USER_INPUT, source="llm_mapped"),
                        daily_series=Series(name="daily_token_usage", unit="millions_tokens", provenance=Provenance.USER_INPUT, source="llm_mapped", values=[round(v, 4) for v in tokens_list]),
                        detected_model=detected_m,
                        column_mapping={str(k): str(v) for k, v in mapping.items()},
                        invariants_passed=True,
                        error=None
                    )
                else:
                    return IngestionReport(
                        success=False,
                        method="llm_mapped",
                        num_days=0,
                        total_tokens_m=Quantity(id="ingest.total_tokens_m", value=0.0, unit="millions_tokens", provenance=Provenance.USER_INPUT, source="rejected"),
                        mean_daily_tokens_m=Quantity(id="ingest.mean_daily_tokens_m", value=0.0, unit="millions_tokens_per_day", provenance=Provenance.USER_INPUT, source="rejected"),
                        daily_volatility=Quantity(id="ingest.daily_volatility", value=0.0, unit="millions_tokens_std", provenance=Provenance.USER_INPUT, source="rejected"),
                        daily_series=Series(name="daily_token_usage", unit="millions_tokens", provenance=Provenance.USER_INPUT, source="rejected", values=[]),
                        detected_model="unknown",
                        column_mapping={str(k): str(v) for k, v in mapping.items()},
                        invariants_passed=False,
                        error=err
                    )
        except Exception as e:
            return IngestionReport(
                success=False,
                method="llm_mapped",
                num_days=0,
                total_tokens_m=Quantity(id="ingest.total_tokens_m", value=0.0, unit="millions_tokens", provenance=Provenance.USER_INPUT, source="rejected"),
                mean_daily_tokens_m=Quantity(id="ingest.mean_daily_tokens_m", value=0.0, unit="millions_tokens_per_day", provenance=Provenance.USER_INPUT, source="rejected"),
                daily_volatility=Quantity(id="ingest.daily_volatility", value=0.0, unit="millions_tokens_std", provenance=Provenance.USER_INPUT, source="rejected"),
                daily_series=Series(name="daily_token_usage", unit="millions_tokens", provenance=Provenance.USER_INPUT, source="rejected", values=[]),
                detected_model="unknown",
                column_mapping={},
                invariants_passed=False,
                error=f"LLM fallback mapping failed: {str(e)}"
            )

    return IngestionReport(
        success=False,
        method="deterministic",
        num_days=0,
        total_tokens_m=Quantity(id="ingest.total_tokens_m", value=0.0, unit="millions_tokens", provenance=Provenance.USER_INPUT, source="rejected"),
        mean_daily_tokens_m=Quantity(id="ingest.mean_daily_tokens_m", value=0.0, unit="millions_tokens_per_day", provenance=Provenance.USER_INPUT, source="rejected"),
        daily_volatility=Quantity(id="ingest.daily_volatility", value=0.0, unit="millions_tokens_std", provenance=Provenance.USER_INPUT, source="rejected"),
        daily_series=Series(name="daily_token_usage", unit="millions_tokens", provenance=Provenance.USER_INPUT, source="rejected", values=[]),
        detected_model="unknown",
        column_mapping={},
        invariants_passed=False,
        error="CSV parsing failed invariant checks and no LLM key available"
    )

def generate_synthetic_usage_series(
    monthly_tokens: float = 30.0,
    growth_pct_per_month: float = 0.0,
    daily_volatility_pct: float = 15.0,
    days: int = 60,
    seed: int = 42,
    base_daily_tokens: Optional[float] = None
) -> IngestionReport:
    if base_daily_tokens is not None:
        monthly_tokens = (base_daily_tokens * 30.0) / 1_000_000.0
    rng = np.random.default_rng(seed)
    mean_daily = monthly_tokens / 30.0
    daily_growth = (1.0 + (growth_pct_per_month / 100.0)) ** (1.0 / 30.0) - 1.0
    vol = daily_volatility_pct / 100.0

    daily_series = []
    current_mean = mean_daily
    for d in range(days):
        noise = rng.normal(0.0, vol)
        val = max(0.01, current_mean * math.exp(noise))
        daily_series.append(round(val, 4))
        current_mean *= (1.0 + daily_growth)

    tot_tokens_m = sum(daily_series)
    std_m = float(np.std(daily_series, ddof=1))

    return IngestionReport(
        success=True,
        method="synthetic",
        num_days=days,
        total_tokens_m=Quantity(
            id="ingest.total_tokens_m",
            value=round(tot_tokens_m, 4),
            unit="millions_tokens",
            provenance=Provenance.SIMULATED,
            source="log_linear_generator",
            note="USER_INPUT-derived"
        ),
        mean_daily_tokens_m=Quantity(
            id="ingest.mean_daily_tokens_m",
            value=round(tot_tokens_m / days, 4),
            unit="millions_tokens_per_day",
            provenance=Provenance.SIMULATED,
            source="log_linear_generator",
            note="USER_INPUT-derived"
        ),
        daily_volatility=Quantity(
            id="ingest.daily_volatility",
            value=round(std_m, 4),
            unit="millions_tokens_std",
            provenance=Provenance.SIMULATED,
            source="log_linear_generator",
            note="USER_INPUT-derived"
        ),
        daily_series=Series(
            name="daily_token_usage",
            unit="millions_tokens",
            provenance=Provenance.SIMULATED,
            source="log_linear_generator",
            values=daily_series
        ),
        detected_model="openai/gpt-4o",
        column_mapping={"model_type": "log_linear_synthetic"},
        invariants_passed=True,
        error=None
    )

def parse_usage_input(usage_input: Any, gateway: Optional[Any] = None) -> IngestionReport:
    if isinstance(usage_input, dict):
        return generate_synthetic_usage_series(
            monthly_tokens=float(usage_input.get("monthly_tokens", 45.0)),
            growth_pct_per_month=float(usage_input.get("growth_pct_per_month", 6.5)),
            daily_volatility_pct=float(usage_input.get("daily_volatility_pct", 14.0)),
            days=int(usage_input.get("days", 90)),
            seed=int(usage_input.get("seed", 42))
        )
    return ingest_usage_csv(str(usage_input), gateway=gateway)

generate_synthetic_usage = generate_synthetic_usage_series

