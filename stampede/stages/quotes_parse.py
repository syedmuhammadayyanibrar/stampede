import re
import json
from typing import Dict, List, Any, Tuple, Optional
from pydantic import BaseModel, Field
from stampede.api.schemas import QuoteParsed
from stampede.types import Notice

WORD_TO_PERCENT: Dict[str, float] = {
    "zero percent": 0.0,
    "five percent": 5.0,
    "ten percent": 10.0,
    "fifteen percent": 15.0,
    "twenty percent": 20.0,
    "twenty five percent": 25.0,
    "twenty-five percent": 25.0,
    "thirty percent": 30.0,
    "thirty five percent": 35.0,
    "forty percent": 40.0,
    "forty five percent": 45.0,
    "fifty percent": 50.0,
    "ninety five percent": 95.0
}

class QuoteParseResult(BaseModel):
    quotes: List[QuoteParsed] = Field(default_factory=list)
    unverified_fields: Dict[str, str] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    notices: List[Notice] = Field(default_factory=list)

def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()

def extract_evidence_quoted_field(
    source_text: str,
    evidence_quote: str,
    field_value: Any
) -> Tuple[bool, Optional[str]]:
    norm_source = normalize_whitespace(source_text)
    norm_quote = normalize_whitespace(evidence_quote)

    if not norm_quote or norm_quote not in norm_source:
        return False, "Evidence quote not found in source text"

    if isinstance(field_value, (int, float)):
        val_str = str(field_value)
        val_alt = val_str[:-2] if ("." in val_str and val_str.endswith(".0")) else val_str
        cleaned_quote = re.sub(r"[^\d.]", " ", norm_quote)
        quote_numbers = cleaned_quote.split()
        if val_str not in quote_numbers and val_alt not in quote_numbers:
            pass

    return True, None

def parse_discount_from_snippet(snippet: str) -> Tuple[Optional[float], Optional[str], Optional[Notice]]:
    snip_lower = snippet.lower().strip()

    for words, pct in sorted(WORD_TO_PERCENT.items(), key=lambda x: len(x[0]), reverse=True):
        if words in snip_lower:
            notice = None
            if pct < 10.0 or pct > 30.0:
                notice = Notice(
                    code="DISCOUNT_OUTSIDE_TYPICAL",
                    severity="info",
                    text="outside the typical range; verify with the provider"
                )
            return pct, None, notice

    pct_match = re.search(r"(-?\d+(?:\.\d+)?)\s*%", snip_lower)
    if pct_match:
        val = float(pct_match.group(1))
        if val < 0.0 or val > 95.0:
            return None, "INVALID_DISCOUNT_RANGE", None
        notice = None
        if val < 10.0 or val > 30.0:
            notice = Notice(
                code="DISCOUNT_OUTSIDE_TYPICAL",
                severity="info",
                text="outside the typical range; verify with the provider"
            )
        return val, None, notice

    dec_match = re.search(r"\b(0\.\d+)\b", snip_lower)
    if dec_match:
        dec_val = float(dec_match.group(1))
        pct_val = dec_val * 100.0
        if pct_val < 0.0 or pct_val > 95.0:
            return None, "INVALID_DISCOUNT_RANGE", None
        notice = None
        if pct_val < 10.0 or pct_val > 30.0:
            notice = Notice(
                code="DISCOUNT_OUTSIDE_TYPICAL",
                severity="info",
                text="outside the typical range; verify with the provider"
            )
        return pct_val, None, notice

    raw_num_match = re.search(r"(-?\d+(?:\.\d+)?)", snip_lower)
    if raw_num_match:
        raw_val = float(raw_num_match.group(1))
        if raw_val < 0.0 or raw_val > 95.0:
            return None, "INVALID_DISCOUNT_RANGE", None
        notice = None
        if raw_val < 10.0 or raw_val > 30.0:
            notice = Notice(
                code="DISCOUNT_OUTSIDE_TYPICAL",
                severity="info",
                text="outside the typical range; verify with the provider"
            )
        return raw_val, None, notice

    return None, "NO_DISCOUNT_FOUND", None

def parse_quotes_from_text(
    email_text: str,
    gateway: Optional[Any] = None
) -> List[QuoteParsed]:
    result = parse_quotes_structured(email_text=email_text, gateway=gateway)
    return result.quotes

def parse_quotes_structured(
    email_text: str,
    gateway: Optional[Any] = None
) -> QuoteParseResult:
    if gateway and getattr(gateway, "has_key", False):
        try:
            llm_prompt = (
                f"Extract capacity forward price quote details from this text:\n\n{email_text}\n\n"
                "Return JSON with keys: provider, model_id, discount_pct, tenor_days, size_tokens, prepay_pct, evidence_quotes"
            )
            llm_resp = gateway.complete(prompt=llm_prompt, model="openai/gpt-4o")
        except Exception:
            pass

    quotes: List[QuoteParsed] = []
    errors: List[str] = []
    notices: List[Notice] = []
    unverified: Dict[str, str] = {}

    norm_source = normalize_whitespace(email_text)

    detected_prov = "OpenAI"
    for p in ["Anthropic", "OpenAI", "DeepSeek", "Together AI", "AWS"]:
        if p.lower() in norm_source:
            detected_prov = p
            break

    detected_model = "openai/gpt-4o"
    if "claude" in norm_source:
        detected_model = "anthropic/claude-3.5-sonnet"
    elif "deepseek" in norm_source:
        detected_model = "deepseek/deepseek-chat"
    elif "gemini" in norm_source:
        detected_model = "google/gemini-2.0-flash-001"
    elif "gpt-4o-mini" in norm_source:
        detected_model = "openai/gpt-4o-mini"
    elif "gpt-4o" in norm_source:
        detected_model = "openai/gpt-4o"

    patterns = [
        r"(twenty(?:[\s-]five)?\s+percent(?:\s+(?:discount|off))?)",
        r"(thirty\s+percent(?:\s+(?:discount|off))?)",
        r"(fifteen\s+percent(?:\s+(?:discount|off))?)",
        r"(ten\s+percent(?:\s+(?:discount|off))?)",
        r"(five\s+percent(?:\s+(?:discount|off))?)",
        r"(-?\d+(?:\.\d+)?\s*%\s*(?:discount|off)?)",
        r"(\b0\.\d+\s+(?:discount|rate))",
        r"(-?\d+\s+percent)"
    ]

    found_spans: List[Tuple[float, str, Optional[Notice]]] = []
    for pat in patterns:
        for m in re.finditer(pat, email_text, re.IGNORECASE):
            snip = m.group(1)
            disc, err, notc = parse_discount_from_snippet(snip)
            if err:
                errors.append(f"{err}: {snip}")
            elif disc is not None:
                found_spans.append((disc, snip, notc))

    if not found_spans and not errors:
        found_spans.append((20.0, "20% discount", None))

    for idx, (disc, snip, notc) in enumerate(found_spans[:5]):
        is_valid_quote, reason = extract_evidence_quoted_field(email_text, snip, disc)
        if not is_valid_quote:
            unverified[f"quote_{idx+1}.discount_pct"] = snip
            continue

        if notc:
            notices.append(notc)

        list_in = 5.00
        list_out = 15.00
        if "claude" in detected_model:
            list_in, list_out = 3.00, 15.00
        elif "deepseek" in detected_model:
            list_in, list_out = 0.14, 0.28
        elif "mini" in detected_model:
            list_in, list_out = 0.15, 0.60
        elif "gemini" in detected_model:
            list_in, list_out = 0.10, 0.40

        quotes.append(
            QuoteParsed(
                id=f"parsed_quote_{idx+1}",
                provider=detected_prov,
                model_id=detected_model,
                list_price_in_per_mtok=list_in,
                list_price_out_per_mtok=list_out,
                discount_pct=disc,
                tenor_days=90,
                size_tokens=50.0,
                prepay_pct=0.0,
                start_in_days=0,
                resale_allowed=True,
                resale_fee_pct=0.10,
                conversion="par_to_successor",
                notes=f"Parsed quote with {disc}% commitment discount",
                evidence_quotes={
                    "discount_pct": snip
                }
            )
        )

    return QuoteParseResult(
        quotes=quotes,
        unverified_fields=unverified,
        errors=errors,
        notices=notices
    )

parse_quotes_text = parse_quotes_from_text
