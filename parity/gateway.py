import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx

class CacheMiss(Exception):
    pass

class NoAPIKey(Exception):
    pass

class BudgetExceeded(Exception):
    pass

class LLMGateway:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        cache_dir: Path = Path("data/cache/llm"),
        budget_usd: float = 40.0,
        offline: bool = False,
        session_cache: Optional[Dict[str, Any]] = None
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.base_url = base_url or os.environ.get("PARITY_BASE_URL", "https://openrouter.ai/api/v1")
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.budget_usd = float(os.environ.get("PARITY_BUDGET_USD", str(budget_usd)))
        self.offline = offline or bool(os.environ.get("PARITY_OFFLINE", ""))
        self.total_spend_usd = 0.0
        self.session_cache = session_cache if session_cache is not None else {}

    def compute_cache_key(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict[str, Any]]],
        response_format: Optional[Dict[str, Any]]
    ) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "tools": tools,
            "response_format": response_format
        }
        raw_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw_bytes).hexdigest()

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
        cache_key = self.compute_cache_key(model, messages, temperature, max_tokens, tools, response_format)
        target_session_cache = session_cache if session_cache is not None else self.session_cache

        if cache:
            if cache_scope == "session":
                if cache_key in target_session_cache:
                    return target_session_cache[cache_key]
            else:
                cache_file = self.cache_dir / f"{cache_key}.json"
                if cache_file.exists():
                    with open(cache_file, "r", encoding="utf-8") as f:
                        return json.load(f)

        if self.offline:
            raise CacheMiss(f"Cache miss in offline mode for model {model} (key: {cache_key})")

        if not self.api_key:
            raise NoAPIKey("OPENROUTER_API_KEY not set")

        if self.total_spend_usd >= self.budget_usd:
            raise BudgetExceeded(f"Cumulative spend ${self.total_spend_usd:.4f} exceeded budget ${self.budget_usd:.2f}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/touchmark/stampede",
            "X-Title": "Parity Benchmark",
            "Content-Type": "application/json"
        }

        body: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if tools:
            body["tools"] = tools
        if response_format:
            body["response_format"] = response_format

        start_t = time.perf_counter()
        retries = 3
        backoff = 1.0

        for attempt in range(retries):
            try:
                with httpx.Client(timeout=30.0) as client:
                    resp = client.post(f"{self.base_url}/chat/completions", headers=headers, json=body)
                    if resp.status_code in (429, 500, 502, 503, 504):
                        if attempt == retries - 1:
                            resp.raise_for_status()
                        time.sleep(backoff)
                        backoff *= 2.0
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    break
            except Exception:
                if attempt == retries - 1:
                    raise
                time.sleep(backoff)
                backoff *= 2.0

        latency = time.perf_counter() - start_t
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        choices = data.get("choices", [{}])
        msg = choices[0].get("message", {})
        served_model = data.get("model", model)

        cost_est = (prompt_tokens * 0.000003) + (completion_tokens * 0.000015)
        self.total_spend_usd += cost_est

        result = {
            "content": msg.get("content", ""),
            "tool_calls": msg.get("tool_calls", []),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency_seconds": round(latency, 4),
            "served_model": served_model,
            "requested_model": model,
            "mismatch": served_model != model,
            "tag": tag,
            "timestamp": time.time()
        }

        if cache:
            if cache_scope == "session":
                target_session_cache[cache_key] = result
            elif persist_outputs:
                cache_file = self.cache_dir / f"{cache_key}.json"
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)

        return result
