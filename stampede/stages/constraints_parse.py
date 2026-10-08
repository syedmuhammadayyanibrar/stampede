import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from stampede.types import Quantity, Provenance

class ConstraintItem(BaseModel):
    field: str
    value: Any
    is_hard: bool = True
    evidence_quote: str

class ParsedConstraints(BaseModel):
    items: List[ConstraintItem] = Field(default_factory=list)
    unparsed_remainder: List[str] = Field(default_factory=list)
    raw_text: str = ""
    method: str = "deterministic"

    def get_value(self, field_name: str, default: Any = None) -> Any:
        for c in self.items:
            if c.field == field_name:
                return c.value
        return default

    def to_dict(self) -> Dict[str, Any]:
        res = {}
        for c in self.items:
            res[c.field] = c.value
        return res

def parse_constraints_deterministic(text: str) -> ParsedConstraints:
    items: List[ConstraintItem] = []
    unparsed: List[str] = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    hard_pattern = re.compile(r"\b(must|never|cannot|can\s+not|at\s+most|at\s+least|strictly|required)\b", re.IGNORECASE)

    for line in lines:
        matched = False
        is_hard = bool(hard_pattern.search(line))

        m = re.search(r"(?:exclude|never\s+use|do\s+not\s+use|no)\s+([a-zA-Z0-9_\-]+)", line, re.IGNORECASE)
        if m:
            prov = m.group(1).lower()
            quote = m.group(0)
            items.append(ConstraintItem(field="excluded_providers", value=[prov], is_hard=is_hard, evidence_quote=quote))
            matched = True

        m = re.search(r"(?:only\s+use|allowed\s+models?[:\s]+)([\w\-\,\s]+)", line, re.IGNORECASE)
        if m:
            models = [x.strip() for x in m.group(1).split(",") if x.strip()]
            quote = m.group(0)
            items.append(ConstraintItem(field="allowed_models", value=models, is_hard=is_hard, evidence_quote=quote))
            matched = True

        m = re.search(r"(?:max\s+spend|budget|cannot\s+exceed|cap\s+at)\s*\$?([0-9,]+(?:\.[0-9]+)?)", line, re.IGNORECASE)
        if m:
            val = float(m.group(1).replace(",", ""))
            quote = m.group(0)
            items.append(ConstraintItem(field="max_spend_usd", value=val, is_hard=is_hard, evidence_quote=quote))
            matched = True

        m = re.search(r"(?:min(?:imum)?\s+parity|parity\s*(?:>=|at\s+least))\s*([0-9\.]+)", line, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            quote = m.group(0)
            items.append(ConstraintItem(field="min_parity", value=val, is_hard=is_hard, evidence_quote=quote))
            matched = True

        m = re.search(r"(?:min(?:imum)?\s+tenor|tenor\s*(?:>=|at\s+least))\s*([0-9]+)\s*days?", line, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            quote = m.group(0)
            items.append(ConstraintItem(field="min_tenor_days", value=val, is_hard=is_hard, evidence_quote=quote))
            matched = True

        m = re.search(r"(?:max(?:imum)?\s+tenor|tenor\s*(?:<=|at\s+most))\s*([0-9]+)\s*days?", line, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            quote = m.group(0)
            items.append(ConstraintItem(field="max_tenor_days", value=val, is_hard=is_hard, evidence_quote=quote))
            matched = True

        m = re.search(r"(?:max(?:imum)?\s+prepay|prepay\s*(?:<=|at\s+most))\s*([0-9]+(?:\.[0-9]+)?)\s*%", line, re.IGNORECASE)
        if m:
            val = float(m.group(1)) / 100.0
            quote = m.group(0)
            items.append(ConstraintItem(field="max_prepay_pct", value=val, is_hard=is_hard, evidence_quote=quote))
            matched = True

        m = re.search(r"\b(require(?:s|d)?\s+(?:secondary\s+)?resale|resale\s+(?:clause\s+)?required|must\s+support\s+resale)\b", line, re.IGNORECASE)
        if m:
            quote = m.group(0)
            items.append(ConstraintItem(field="require_resale", value=True, is_hard=True, evidence_quote=quote))
            matched = True

        m = re.search(r"\b(require(?:s|d)?\s+(?:model\s+)?conversion|conversion\s+(?:clause\s+)?required|must\s+convert)\b", line, re.IGNORECASE)
        if m:
            quote = m.group(0)
            items.append(ConstraintItem(field="require_conversion", value=True, is_hard=True, evidence_quote=quote))
            matched = True

        m = re.search(r"(?:max(?:imum)?\s+provider\s+share|single\s+provider\s+at\s+most)\s*([0-9]+(?:\.[0-9]+)?)\s*%", line, re.IGNORECASE)
        if m:
            val = float(m.group(1)) / 100.0
            quote = m.group(0)
            items.append(ConstraintItem(field="max_provider_share", value=val, is_hard=is_hard, evidence_quote=quote))
            matched = True

        m = re.search(r"(?:start\s+by|deliver\s+within)\s*([0-9]+)\s*days?", line, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            quote = m.group(0)
            items.append(ConstraintItem(field="start_by_days", value=val, is_hard=is_hard, evidence_quote=quote))
            matched = True

        if not matched:
            unparsed.append(line)

    valid_items: List[ConstraintItem] = []
    norm_text = " ".join(text.split()).lower()
    for it in items:
        norm_q = " ".join(it.evidence_quote.split()).lower()
        if it.evidence_quote and norm_q in norm_text:
            valid_items.append(it)
        else:
            unparsed.append(f"{it.field}:{it.value} (missing verbatim evidence)")

    return ParsedConstraints(items=valid_items, unparsed_remainder=unparsed, raw_text=text, method="deterministic")

def parse_constraints(text: str, gateway: Optional[Any] = None) -> ParsedConstraints:
    has_key = bool(getattr(gateway, "api_key", None)) or bool(getattr(gateway, "has_key", False))
    if not gateway or not has_key:
        return parse_constraints_deterministic(text)

    try:
        prompt = (
            "Extract constraints from this text as JSON array of objects: "
            "[{'field': '...', 'value': ..., 'is_hard': bool, 'evidence_quote': '...'}]. "
            "Fields: excluded_providers, allowed_models, max_spend_usd, min_parity, min_tenor_days, max_tenor_days, max_prepay_pct, require_resale, require_conversion, max_provider_share, start_by_days. "
            "Every constraint MUST have exact verbatim evidence_quote from text. Text:\n" + text
        )
        msg = [{"role": "user", "content": prompt}]
        resp = gateway.complete(model="openai/gpt-4o-mini", messages=msg, temperature=0.0)
        content = resp.get("content", "") if isinstance(resp, dict) else getattr(resp, "text", "")
        import json
        data = json.loads(content)
        items: List[ConstraintItem] = []
        unparsed: List[str] = []
        norm_text = " ".join(text.split()).lower()
        for d in data:
            quote = d.get("evidence_quote", "")
            norm_q = " ".join(quote.split()).lower()
            if quote and norm_q in norm_text:
                items.append(ConstraintItem(
                    field=d["field"],
                    value=d["value"],
                    is_hard=bool(d.get("is_hard", True)),
                    evidence_quote=quote
                ))
            else:
                unparsed.append(str(d))
        return ParsedConstraints(items=items, unparsed_remainder=unparsed, raw_text=text, method="llm_parsed")
    except Exception:
        return parse_constraints_deterministic(text)
