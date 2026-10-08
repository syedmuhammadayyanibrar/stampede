import time
from typing import Dict, List, Any, Optional, Tuple
from fastapi import Request, HTTPException
from stampede.settings import settings
from stampede.sessions import session_store

class TokenBucket:
    def __init__(self, capacity: int, fill_rate_per_sec: float) -> None:
        self.capacity: float = float(capacity)
        self.tokens: float = float(capacity)
        self.fill_rate: float = fill_rate_per_sec
        self.last_update: float = time.time()

    def consume(self, tokens: float = 1.0) -> bool:
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

class RateLimiter:
    def __init__(self) -> None:
        self.read_buckets: Dict[str, TokenBucket] = {}
        self.run_buckets: Dict[str, TokenBucket] = {}

    def check_read(self, client_ip: str) -> bool:
        if client_ip not in self.read_buckets:
            self.read_buckets[client_ip] = TokenBucket(
                capacity=settings.rate_limit_reads_per_min,
                fill_rate_per_sec=settings.rate_limit_reads_per_min / 60.0
            )
        return self.read_buckets[client_ip].consume(1.0)

    def check_run(self, client_ip: str) -> bool:
        if client_ip not in self.run_buckets:
            self.run_buckets[client_ip] = TokenBucket(
                capacity=settings.rate_limit_runs_per_hour,
                fill_rate_per_sec=settings.rate_limit_runs_per_hour / 3600.0
            )
        return self.run_buckets[client_ip].consume(1.0)

    def reset(self) -> None:
        self.read_buckets.clear()
        self.run_buckets.clear()

rate_limiter = RateLimiter()

def validate_workload_input(prompts: List[Dict[str, Any]]) -> None:
    n = len(prompts)
    if n < settings.prompts_min or n > settings.prompts_max:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_PROMPT_COUNT",
                "message": f"Prompts count must be between {settings.prompts_min} and {settings.prompts_max}, received {n}",
                "detail": {"count": n}
            }
        )
    for idx, p in enumerate(prompts):
        text = p.get("text", "")
        if len(text) > settings.prompt_max_chars:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "PROMPT_TOO_LONG",
                    "message": f"Prompt at index {idx} exceeds max length {settings.prompt_max_chars}",
                    "detail": {"index": idx, "length": len(text)}
                }
            )

def validate_models_input(candidates: List[str], incumbent: str) -> None:
    if len(candidates) > settings.max_candidates:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TOO_MANY_CANDIDATES",
                "message": f"At most {settings.max_candidates} candidates allowed",
                "detail": {"count": len(candidates)}
            }
        )
    if not incumbent:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MISSING_INCUMBENT",
                "message": "Incumbent model must be specified",
                "detail": {}
            }
        )

def validate_usage_csv_size(size_bytes: int) -> None:
    if size_bytes > settings.usage_csv_max_bytes:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "CSV_TOO_LARGE",
                "message": f"CSV payload exceeds size limit of {settings.usage_csv_max_bytes} bytes",
                "detail": {"size": size_bytes}
            }
        )

def validate_quote_text_length(length: int) -> None:
    if length > settings.quote_max_chars:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "QUOTE_TOO_LONG",
                "message": f"Quote email text exceeds limit of {settings.quote_max_chars} characters",
                "detail": {"length": length}
            }
        )

def wrap_untrusted_input(tag: str, content: str) -> str:
    escaped = content.replace("<", "&lt;").replace(">", "&gt;")
    return f"<untrusted_data tag=\"{tag}\">\n{escaped}\n</untrusted_data>"
