import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx
from data_sources.openrouter import get_openrouter_api_key
from parity.spend_tracker import SpendTracker
from parity.io import write_json_atomic, read_json

class OpenRouterClient:
    def __init__(
        self,
        cache_dir: Path = Path("data/parity/llm_cache"),
        spend_tracker: Optional[SpendTracker] = None,
        timeout_seconds: float = 30.0
    ) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.spend_tracker = spend_tracker or SpendTracker()
        self.timeout_seconds = timeout_seconds
        self.api_key = get_openrouter_api_key()

    def _get_cache_key(self, model: str, prompt: str, temperature: float) -> str:
        payload = f"{model}:{temperature}:{prompt}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 512,
        call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        cache_key = self._get_cache_key(model, prompt, temperature)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            return read_json(cache_file)

        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set.")

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/stampede-parity",
            "X-Title": "Parity Substitutability Engine"
        }
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        with httpx.Client(timeout=self.timeout_seconds) as client:
            resp = client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()

        choices = data.get("choices", [])
        content = choices[0]["message"]["content"].strip() if choices else ""
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", max(1, len(prompt) // 4))
        completion_tokens = usage.get("completion_tokens", max(1, len(content) // 4))

        cost = self.spend_tracker.record_call_spend(
            call_id=call_id or cache_key[:12],
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            is_ceiling_check=False
        )

        result = {
            "content": content,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": cost,
            "cache_key": cache_key
        }
        write_json_atomic(cache_file, result)
        return result
