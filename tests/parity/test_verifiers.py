from parity.substitutability.verifiers import (
    verify_code_generation,
    verify_json_extraction,
    verify_math_reasoning,
    verify_classification,
    verify_translation,
    evaluate_verifiable_item
)

def test_code_verifier_passes() -> None:
    code = "def solve_test(n: int) -> int:\n    return sum((2*i + 1)**2 for i in range(n))"
    cases = [{"input": 1, "expected": 1}, {"input": 3, "expected": 35}]
    assert verify_code_generation(code, "solve_test", cases) is True

def test_code_verifier_fails_on_wrong_output() -> None:
    code = "def solve_test(n: int) -> int:\n    return n"
    cases = [{"input": 3, "expected": 35}]
    assert verify_code_generation(code, "solve_test", cases) is False

def test_json_verifier() -> None:
    raw = "```json\n{\"customer_name\": \"Acme\", \"order_id\": \"123\", \"total_usd\": 50.0}\n```"
    schema = {"required": ["customer_name", "order_id", "total_usd"]}
    expected = {"customer_name": "Acme", "order_id": "123", "total_usd": 50.0}
    assert verify_json_extraction(raw, schema, expected) is True

def test_math_verifier() -> None:
    text = "The final calculated answer is 42."
    assert verify_math_reasoning(text, 42) is True
    assert verify_math_reasoning(text, 100) is False

def test_classification_verifier() -> None:
    text = "The category is LOW_LATENCY_INFERENCE."
    assert verify_classification(text, "LOW_LATENCY_INFERENCE") is True
    assert verify_classification("BATCH_OFFLINE_TRAINING", "LOW_LATENCY_INFERENCE") is False

def test_evaluate_verifiable_item_dispatch() -> None:
    meta = {"expected_value": 85}
    assert evaluate_verifiable_item("reasoning_math", "Result = 85", meta) is True
