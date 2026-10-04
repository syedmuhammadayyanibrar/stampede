import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx
from data_sources.openrouter import get_openrouter_api_key
from parity.spend_tracker import SpendTracker

CEILING_PROMPTS = [
    {"id": "ceil_001", "model": "openai/gpt-4o-mini", "prompt": "Output the single word 'PARITY_READY'."},
    {"id": "ceil_002", "model": "deepseek/deepseek-chat", "prompt": "Solve 17 + 25. Output only the integer result."},
    {"id": "ceil_003", "model": "openai/gpt-4o-mini", "prompt": "Classify the sentiment of 'System performance is outstanding': POSITIVE, NEGATIVE, or NEUTRAL. Output only the category."},
    {"id": "ceil_004", "model": "google/gemini-2.5-flash-lite", "prompt": "Translate 'Risk management' into French. Output only the translation."},
    {"id": "ceil_005", "model": "openai/gpt-4o-mini", "prompt": "Extract JSON: Name=Alice, Role=Quant. Schema: {\"name\": str, \"role\": str}. Output valid JSON only."}
]

def execute_openrouter_call(
    api_key: str,
    model: str,
    prompt: str,
    max_tokens: int = 50
) -> Dict[str, Any]:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/stampede-parity",
        "X-Title": "Parity Risk Engine"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.0
    }
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        res = resp.json()
        usage = res.get("usage", {})
        choices = res.get("choices", [])
        content = choices[0]["message"]["content"].strip() if choices else ""
        return {
            "content": content,
            "prompt_tokens": usage.get("prompt_tokens", max(1, len(prompt) // 4)),
            "completion_tokens": usage.get("completion_tokens", max(1, len(content) // 4))
        }

def run_ceiling_check(tracker: Optional[SpendTracker] = None) -> Dict[str, Any]:
    api_key = get_openrouter_api_key()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured in environment or .env")

    sp_tracker = tracker or SpendTracker()
    results = []

    for item in CEILING_PROMPTS:
        cid = item["id"]
        model = item["model"]
        prompt = item["prompt"]

        response = execute_openrouter_call(api_key, model, prompt)
        cost = sp_tracker.record_call_spend(
            call_id=cid,
            model=model,
            prompt_tokens=response["prompt_tokens"],
            completion_tokens=response["completion_tokens"],
            is_ceiling_check=True
        )

        results.append({
            "id": cid,
            "model": model,
            "response": response["content"],
            "prompt_tokens": response["prompt_tokens"],
            "completion_tokens": response["completion_tokens"],
            "cost_usd": cost
        })

    total_ceiling_cost = sum(r["cost_usd"] for r in results)
    return {
        "status": "SUCCESS",
        "total_calls": len(results),
        "total_cost_usd": round(total_ceiling_cost, 6),
        "cumulative_spend_usd": sp_tracker.get_cumulative_spend(),
        "calls": results
    }

if __name__ == "__main__":
    res = run_ceiling_check()
    print("CEILING CHECK COMPLETE")
    print(f"Status: {res['status']}")
    print(f"Total calls: {res['total_calls']}")
    print(f"Total cost: ${res['total_cost_usd']:.6f}")
    print(f"Cumulative spend: ${res['cumulative_spend_usd']:.6f}")
    for c in res["calls"]:
        print(f"  [{c['model']}] {c['prompt_tokens']} in / {c['completion_tokens']} out, ${c['cost_usd']:.6f} -> {c['response'][:40]}")
