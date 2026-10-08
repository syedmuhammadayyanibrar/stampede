import math
import json
import hashlib
import socket
from typing import Dict, List, Any, Optional, Tuple
import pytest

class SimModel:
    def __init__(self, model_id: str, base_accuracy: float = 0.85) -> None:
        self.model_id = model_id
        self.base_accuracy = base_accuracy

    def evaluate(self, prompt: str, seed: int = 42) -> Tuple[bool, str, int, int]:
        h = int(hashlib.md5(f"{self.model_id}:{prompt}:{seed}".encode()).hexdigest()[:8], 16)
        prob = (h % 10000) / 10000.0
        success = prob < self.base_accuracy
        prompt_tokens = max(10, len(prompt.split()) * 2)
        completion_tokens = 50 if success else 30
        content = f"Simulated output from {self.model_id} for prompt {prompt[:20]}"
        return success, content, prompt_tokens, completion_tokens

class SimJudge:
    def __init__(self, judge_id: str, sensitivity: float = 0.95, specificity: float = 0.90) -> None:
        self.judge_id = judge_id
        self.sensitivity = sensitivity
        self.specificity = specificity

    def judge_pair(self, gold_outcome: int, order_ab: bool, seed: int = 42) -> int:
        h = int(hashlib.md5(f"{self.judge_id}:{gold_outcome}:{order_ab}:{seed}".encode()).hexdigest()[:8], 16)
        draw = (h % 10000) / 10000.0
        if gold_outcome >= 0:
            called_non_inferior = draw < self.sensitivity
            return 1 if called_non_inferior else -1
        else:
            called_inferior = draw < self.specificity
            return -1 if called_inferior else 1

class FakeGateway:
    def __init__(
        self,
        api_key: str = "fake-test-key",
        budget_usd: float = 10.0,
        offline: bool = False,
        session_cache: Optional[Dict[str, Any]] = None
    ) -> None:
        self.api_key = api_key
        self.budget_usd = budget_usd
        self.offline = offline
        self.total_spend_usd = 0.0
        self.call_count = 0
        self.session_cache = session_cache if session_cache is not None else {}
        self.models = {
            "openai/gpt-4o": SimModel("openai/gpt-4o", 0.92),
            "openai/gpt-4o-mini": SimModel("openai/gpt-4o-mini", 0.88),
            "anthropic/claude-3.5-sonnet": SimModel("anthropic/claude-3.5-sonnet", 0.94),
            "deepseek/deepseek-chat": SimModel("deepseek/deepseek-chat", 0.86),
            "google/gemini-2.0-flash-001": SimModel("google/gemini-2.0-flash-001", 0.87)
        }
        self.judge = SimJudge("meta-llama/llama-3.3-70b-instruct", 0.95, 0.90)

    def compute_cache_key(self, model: str, messages: List[Dict[str, Any]], tools: Optional[List[Any]] = None) -> str:
        raw = f"{model}:{json.dumps(messages, sort_keys=True)}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def complete(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.0,
        max_tokens: int = 1000,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        cache: bool = True,
        tag: str = "",
        cache_scope: str = "disk",
        persist_outputs: bool = True,
        session_cache: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        key = self.compute_cache_key(model, messages, tools)
        target_cache = session_cache if session_cache is not None else self.session_cache

        if cache and key in target_cache:
            return target_cache[key]

        cost = 0.0001
        if self.total_spend_usd + cost > self.budget_usd:
            raise Exception("BudgetExceeded in FakeGateway")

        self.call_count += 1
        self.total_spend_usd += cost

        last_prompt = messages[-1].get("content", "") if messages else ""
        sim = self.models.get(model, SimModel(model, 0.85))
        _, content, pt, ct = sim.evaluate(last_prompt)

        res = {
            "content": content,
            "tool_calls": [],
            "prompt_tokens": pt,
            "completion_tokens": ct,
            "latency_seconds": 0.05,
            "served_model": model,
            "requested_model": model,
            "mismatch": False,
            "tag": tag
        }

        if cache:
            target_cache[key] = res

        return res

@pytest.fixture(autouse=False)
def block_network_sockets(monkeypatch):
    def guarded_connect(*args, **kwargs):
        raise RuntimeError("Network socket call blocked in test environment")
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
