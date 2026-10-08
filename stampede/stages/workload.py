import re
import json
import jsonschema
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel
from stampede.api.schemas import PromptItem, PromptCheck
from stampede.types import Quantity, Provenance

class CheckEvaluator:
    @staticmethod
    def evaluate_check(output_text: str, check: Any) -> bool:
        if isinstance(check, dict):
            target = str(check.get("target") or check.get("expected") or "")
            ctype = str(check.get("check_type") or check.get("type") or "exact_match")
        else:
            target = str(getattr(check, "target", ""))
            ctype = str(getattr(check, "check_type", "exact_match"))
        if ctype == "exact_match":
            return output_text.strip() == target.strip()
        elif ctype == "must_contain":
            return target.lower() in output_text.lower()
        elif ctype == "must_not_contain":
            return target.lower() not in output_text.lower()
        elif ctype in ("regex_must_match", "regex_match"):
            try:
                return bool(re.search(target, output_text, re.IGNORECASE))
            except Exception:
                return False
        elif ctype == "max_words":
            try:
                max_w = int(target)
                return len(output_text.split()) <= max_w
            except Exception:
                return False
        elif ctype == "json_schema":
            try:
                parsed = json.loads(output_text)
                schema = json.loads(target) if isinstance(target, str) and target.strip().startswith("{") else target
                if isinstance(schema, dict):
                    jsonschema.validate(instance=parsed, schema=schema)
                    return True
                return isinstance(parsed, dict)
            except Exception:
                return False
        return True

    @classmethod
    def score_output(cls, output_text: str, checks: Optional[List[PromptCheck]]) -> float:
        if not checks:
            return 1.0
        passed = sum(1 for chk in checks if cls.evaluate_check(output_text, chk))
        return float(passed / len(checks))

class WorkloadPayload(BaseModel):
    mode: str
    num_prompts: int
    prompts: List[PromptItem]
    description: Optional[str] = None
    input_output_ratio: float = 3.0

    def __iter__(self):
        return iter(self.prompts)

    def __len__(self):
        return len(self.prompts)

    def __getitem__(self, idx):
        return self.prompts[idx]

def inspect_workload_mode(prompts: List[PromptItem]) -> str:
    has_checks = all(p.checks is not None and len(p.checks) > 0 for p in prompts)
    return "checked" if has_checks else "judged"

def generate_synthetic_workload(description: str = "general", count: Optional[int] = None, n: int = 10) -> WorkloadPayload:
    eff_n = count if count is not None else n
    prompts = []
    for i in range(1, eff_n + 1):
        p_text = f"Synthetic prompt #{i} evaluating domain: {description} (Task verification #{i})"
        checks = [
            PromptCheck(check_type="must_contain", target="Task"),
            PromptCheck(check_type="max_words", target="200")
        ]
        prompts.append(PromptItem(text=p_text, checks=checks))
    return WorkloadPayload(
        mode="checked",
        num_prompts=eff_n,
        prompts=prompts,
        description=description,
        input_output_ratio=3.0
    )

def evaluate_task_checks(output_text: str, checks: Optional[List[PromptCheck]]) -> bool:
    return CheckEvaluator.score_output(output_text, checks) >= 1.0
