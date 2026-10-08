import json
from stampede.api.schemas import PromptCheck
from stampede.stages.workload import CheckEvaluator

def test_exact_match_verifier():
    chk = PromptCheck(check_type="exact_match", target="hello world")
    assert CheckEvaluator.evaluate_check("hello world", chk) is True
    assert CheckEvaluator.evaluate_check("  hello world \n", chk) is True
    assert CheckEvaluator.evaluate_check("hello", chk) is False
    assert CheckEvaluator.evaluate_check("", chk) is False

def test_must_contain_and_must_not_contain():
    chk_contain = PromptCheck(check_type="must_contain", target="GPU")
    chk_not_contain = PromptCheck(check_type="must_not_contain", target="guaranteed")

    assert CheckEvaluator.evaluate_check("Deploying on NVIDIA GPU clusters", chk_contain) is True
    assert CheckEvaluator.evaluate_check("Deploying on CPU clusters", chk_contain) is False
    assert CheckEvaluator.evaluate_check("Deploying on GPU clusters", chk_not_contain) is True
    assert CheckEvaluator.evaluate_check("High throughput guaranteed by SLA", chk_not_contain) is False

def test_regex_must_match():
    chk_re = PromptCheck(check_type="regex_must_match", target=r"invoice\s*#\d{4}")
    assert CheckEvaluator.evaluate_check("Found Invoice #4812 in receipt", chk_re) is True
    assert CheckEvaluator.evaluate_check("Invoice ID pending", chk_re) is False
    assert CheckEvaluator.evaluate_check("", chk_re) is False

def test_max_words():
    chk_words = PromptCheck(check_type="max_words", target="5")
    assert CheckEvaluator.evaluate_check("one two three four five", chk_words) is True
    assert CheckEvaluator.evaluate_check("one two three", chk_words) is True
    assert CheckEvaluator.evaluate_check("one two three four five six", chk_words) is False
    assert CheckEvaluator.evaluate_check("", chk_words) is True

def test_json_schema_verifier():
    schema = {
        "type": "object",
        "properties": {
            "model": {"type": "string"},
            "tokens": {"type": "integer", "minimum": 1}
        },
        "required": ["model", "tokens"]
    }
    schema_str = json.dumps(schema)
    chk_schema = PromptCheck(check_type="json_schema", target=schema_str)

    valid_json = json.dumps({"model": "gpt-4o", "tokens": 150})
    assert CheckEvaluator.evaluate_check(valid_json, chk_schema) is True

    schema_violation = json.dumps({"model": "gpt-4o", "tokens": -5})
    assert CheckEvaluator.evaluate_check(schema_violation, chk_schema) is False

    missing_field = json.dumps({"model": "gpt-4o"})
    assert CheckEvaluator.evaluate_check(missing_field, chk_schema) is False

    malformed_json = '{"model": "gpt-4o", tokens: 150}'
    assert CheckEvaluator.evaluate_check(malformed_json, chk_schema) is False
    assert CheckEvaluator.evaluate_check("", chk_schema) is False

def test_unicode_and_special_characters():
    chk_unicode = PromptCheck(check_type="must_contain", target="€1,200")
    assert CheckEvaluator.evaluate_check("Total spend is €1,200 for token allotment", chk_unicode) is True
    assert CheckEvaluator.evaluate_check("Total spend is $1,200", chk_unicode) is False

    chk_cjk = PromptCheck(check_type="exact_match", target="東京クラスタ")
    assert CheckEvaluator.evaluate_check("東京クラスタ", chk_cjk) is True
    assert CheckEvaluator.evaluate_check("京都クラスタ", chk_cjk) is False

def test_fractional_prompt_score():
    checks = [
        PromptCheck(check_type="must_contain", target="valid"),
        PromptCheck(check_type="must_not_contain", target="fail"),
        PromptCheck(check_type="max_words", target="10"),
        PromptCheck(check_type="regex_must_match", target=r"\d+")
    ]
    score_all = CheckEvaluator.score_output("valid text with 42 words", checks)
    assert score_all == 1.0

    score_half = CheckEvaluator.score_output("valid text that should fail now", checks)
    assert score_half == 0.5
