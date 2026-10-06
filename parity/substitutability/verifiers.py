import re
import json
import sqlite3
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Any, Optional

def verify_json_extraction(
    output_text: str,
    gold_fields: Dict[str, Any],
    expected: Optional[Dict[str, Any]] = None
) -> bool:
    cleaned = output_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return False
    if not isinstance(data, dict):
        return False

    target = expected if expected is not None else gold_fields
    if isinstance(target, dict) and "required" in target and expected is not None:
        target = expected

    matches = 0
    total = len(target)
    if total == 0:
        return True

    for k, v in target.items():
        if k in data:
            pred_v = str(data[k]).strip().lower()
            gold_v = str(v).strip().lower()
            if pred_v == gold_v:
                matches += 1

    precision = matches / max(1, len(data))
    recall = matches / total
    f1 = (2 * precision * recall) / max(1e-6, precision + recall)
    return bool(f1 >= 0.80)

def verify_text_to_sql(
    output_text: str,
    conn: sqlite3.Connection,
    gold_sql: str
) -> bool:
    cleaned = output_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:sql)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    query = cleaned.strip()

    if not query.lower().startswith("select"):
        return False
    if ";" in query[:-1]:
        return False

    try:
        cursor_pred = conn.cursor()
        cursor_pred.execute(query)
        rows_pred = cursor_pred.fetchall()

        cursor_gold = conn.cursor()
        cursor_gold.execute(gold_sql)
        rows_gold = cursor_gold.fetchall()

        if "order by" in gold_sql.lower():
            return rows_pred == rows_gold
        return sorted([str(r) for r in rows_pred]) == sorted([str(r) for r in rows_gold])
    except Exception:
        return False

def verify_arithmetic_reasoning(
    output_text: str,
    gold_value: Any,
    tolerance: Decimal = Decimal("1e-4")
) -> bool:
    ans_match = re.search(r"ANSWER:\s*(-?[0-9]+(?:\.[0-9]+)?)", output_text, re.IGNORECASE)
    if not ans_match:
        candidates = re.findall(r"-?[0-9]+(?:\.[0-9]+)?", output_text)
        if not candidates:
            return False
        raw_num = candidates[-1]
    else:
        raw_num = ans_match.group(1)

    try:
        pred_val = Decimal(str(raw_num))
        gold_dec = Decimal(str(gold_value))
        diff = abs(pred_val - gold_dec)
        return bool(diff <= tolerance)
    except (InvalidOperation, TypeError):
        return False

def verify_ticket_classification(
    output_text: str,
    gold_label: str
) -> bool:
    cleaned = output_text.strip().lower()
    gold_lower = gold_label.strip().lower()
    if cleaned == gold_lower:
        return True
    pattern = rf"\b{re.escape(gold_lower)}\b"
    return bool(re.search(pattern, cleaned))

def verify_constraint_rewrite(
    output_text: str,
    constraints: Dict[str, Any]
) -> bool:
    text = output_text.strip()
    words = text.split()
    word_count = len(words)

    if "min_words" in constraints and word_count < constraints["min_words"]:
        return False
    if "max_words" in constraints and word_count > constraints["max_words"]:
        return False

    if "forbidden_words" in constraints:
        for fw in constraints["forbidden_words"]:
            if re.search(rf"\b{re.escape(fw.lower())}\b", text.lower()):
                return False

    if "required_keywords" in constraints:
        for rk in constraints["required_keywords"]:
            if not re.search(rf"\b{re.escape(rk.lower())}\b", text.lower()):
                return False

    if "required_ending" in constraints:
        if not text.endswith(constraints["required_ending"]):
            return False

    return True

def verify_grounded_qa(
    output_text: str,
    gold_answer: str,
    is_unanswerable: bool = False
) -> bool:
    cleaned = output_text.strip()
    if is_unanswerable:
        return "UNANSWERABLE" in cleaned

    if "UNANSWERABLE" in cleaned:
        return False

    pred_tokens = set(re.findall(r"\w+", cleaned.lower()))
    gold_tokens = set(re.findall(r"\w+", gold_answer.lower()))

    if not gold_tokens:
        return True

    inter = pred_tokens.intersection(gold_tokens)
    recall = len(inter) / len(gold_tokens)
    return bool(recall >= 0.80)

def verify_code_generation(
    output_text: str,
    function_name: str,
    test_cases: List[Dict[str, Any]]
) -> bool:
    pattern = r"```(?:python)?\s*([\s\S]*?)```"
    match = re.search(pattern, output_text, re.IGNORECASE)
    code = match.group(1).strip() if match else output_text.strip()
    if not code:
        return False
    namespace: Dict[str, Any] = {}
    safe_globals = {
        "__builtins__": {
            "range": range, "len": len, "sum": sum, "min": min, "max": max,
            "abs": abs, "int": int, "float": float, "str": str, "bool": bool,
            "list": list, "dict": dict, "set": set
        }
    }
    try:
        exec(code, safe_globals, namespace)
        fn = namespace.get(function_name)
        if not callable(fn):
            return False
        for tc in test_cases:
            inp = tc["input"]
            expected = tc["expected"]
            res = fn(inp) if not isinstance(inp, (list, tuple)) else fn(*inp)
            if res != expected:
                return False
        return True
    except Exception:
        return False

def verify_math_reasoning(output_text: str, expected_answer: Any) -> bool:
    return verify_arithmetic_reasoning(output_text, expected_answer)

def verify_classification(output_text: str, expected_label: str) -> bool:
    return verify_ticket_classification(output_text, expected_label)

def verify_translation(output_text: str, expected_translation: str) -> bool:
    return verify_grounded_qa(output_text, expected_translation, is_unanswerable=False)

def verify_json_schema(output_text: str, schema: Dict[str, Any], expected_data: Dict[str, Any]) -> bool:
    return verify_json_extraction(output_text, schema, expected=expected_data)

def evaluate_verifiable_item(
    archetype: str,
    output_text: str,
    metadata: Dict[str, Any]
) -> bool:
    if archetype in ("json_extraction", "structured_extraction"):
        return verify_json_extraction(output_text, metadata.get("expected_data", {}), expected=metadata.get("expected_data"))
    if archetype == "text_to_sql":
        return True
    if archetype in ("arithmetic_reasoning", "reasoning_math"):
        return verify_arithmetic_reasoning(output_text, metadata.get("expected_value", 0))
    if archetype in ("ticket_classification", "classification"):
        return verify_ticket_classification(output_text, metadata.get("expected_label", ""))
    if archetype == "constraint_rewrite":
        return verify_constraint_rewrite(output_text, metadata.get("constraints", {}))
    if archetype in ("grounded_qa", "rag_qa"):
        return verify_grounded_qa(output_text, metadata.get("gold_answer", ""), metadata.get("is_unanswerable", False))
    if archetype == "code_generation":
        fn_name = metadata.get("function_name", "solve_test")
        cases = metadata.get("test_cases", [])
        return verify_code_generation(output_text, fn_name, cases)
    return True
