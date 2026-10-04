import re
import json
import ast
from typing import Dict, List, Any, Optional

def extract_code_block(text: str) -> str:
    pattern = r"```(?:python)?\s*([\s\S]*?)```"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()

def verify_code_generation(
    output_text: str,
    function_name: str,
    test_cases: List[Dict[str, Any]]
) -> bool:
    code = extract_code_block(output_text)
    if not code:
        return False
    try:
        parsed = ast.parse(code)
    except SyntaxError:
        return False

    has_target = any(
        isinstance(node, ast.FunctionDef) and node.name == function_name
        for node in ast.walk(parsed)
    )
    if not has_target:
        return False

    namespace: Dict[str, Any] = {}
    safe_globals = {
        "__builtins__": {
            "range": range,
            "len": len,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "list": list,
            "dict": dict,
            "set": set
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
            if isinstance(inp, list):
                res = fn(*inp)
            elif isinstance(inp, dict):
                res = fn(**inp)
            else:
                res = fn(inp)
            if res != expected:
                return False
        return True
    except Exception:
        return False

def verify_json_extraction(
    output_text: str,
    schema: Dict[str, Any],
    expected_values: Optional[Dict[str, Any]] = None
) -> bool:
    json_pattern = r"\{[\s\S]*\}"
    match = re.search(json_pattern, output_text)
    if not match:
        return False
    try:
        data = json.loads(match.group(0))
        if not isinstance(data, dict):
            return False
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                return False
        if expected_values:
            for k, exp in expected_values.items():
                if data.get(k) != exp:
                    return False
        return True
    except Exception:
        return False

def verify_math_reasoning(output_text: str, expected_value: int) -> bool:
    clean = re.sub(r",(?=\d{3})", "", output_text)
    numbers = re.findall(r"-?\b\d+\b", clean)
    if not numbers:
        return False
    last_num = int(numbers[-1])
    if last_num == expected_value:
        return True
    return any(int(n) == expected_value for n in numbers)

def verify_classification(output_text: str, expected_category: str) -> bool:
    upper = output_text.upper()
    return expected_category.upper() in upper

def verify_translation(output_text: str, reference_text: str) -> bool:
    def tokenize(s: str) -> set[str]:
        return set(re.findall(r"\w+", s.lower()))
    toks_out = tokenize(output_text)
    toks_ref = tokenize(reference_text)
    if not toks_ref:
        return False
    overlap = len(toks_out.intersection(toks_ref)) / len(toks_ref)
    return overlap >= 0.70

def evaluate_verifiable_item(
    archetype: str,
    candidate_output: str,
    metadata: Dict[str, Any]
) -> bool:
    if archetype == "code_generation":
        return verify_code_generation(
            output_text=candidate_output,
            function_name=metadata.get("function_name", "solve"),
            test_cases=metadata.get("test_cases", [])
        )
    elif archetype == "structured_extraction":
        return verify_json_extraction(
            output_text=candidate_output,
            schema=metadata.get("schema", {}),
            expected_values=metadata.get("expected")
        )
    elif archetype == "reasoning_math":
        return verify_math_reasoning(
            output_text=candidate_output,
            expected_value=int(metadata.get("expected_value", 0))
        )
    elif archetype == "classification":
        return verify_classification(
            output_text=candidate_output,
            expected_category=str(metadata.get("expected_category", ""))
        )
    elif archetype == "translation":
        return verify_translation(
            output_text=candidate_output,
            reference_text=str(metadata.get("reference_translation", ""))
        )
    return False
