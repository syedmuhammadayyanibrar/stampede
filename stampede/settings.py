import os
from pathlib import Path
from pydantic import BaseModel

class Settings(BaseModel):
    session_cap_usd: float = float(os.environ.get("STAMPEDE_SESSION_CAP_USD", "2.00"))
    daily_cap_usd: float = float(os.environ.get("STAMPEDE_DAILY_CAP_USD", "25.00"))
    estimate_confirm_threshold_usd: float = float(os.environ.get("STAMPEDE_ESTIMATE_CONFIRM_THRESHOLD_USD", "0.50"))
    session_idle_ttl_seconds: int = int(os.environ.get("STAMPEDE_SESSION_IDLE_TTL_SECONDS", "7200"))
    session_hard_cap_seconds: int = int(os.environ.get("STAMPEDE_SESSION_HARD_CAP_SECONDS", "14400"))
    rate_limit_reads_per_min: int = int(os.environ.get("STAMPEDE_RATE_LIMIT_READS_PER_MIN", "30"))
    rate_limit_runs_per_hour: int = int(os.environ.get("STAMPEDE_RATE_LIMIT_RUNS_PER_HOUR", "3"))
    max_active_runs_per_session: int = 1
    max_active_runs_global: int = 3
    prompts_min: int = 5
    prompts_max: int = 40
    prompt_max_chars: int = 8000
    usage_csv_max_bytes: int = 5 * 1024 * 1024
    max_candidates: int = 3
    quote_max_chars: int = 20000

    def is_killed(self) -> bool:
        if os.environ.get("STAMPEDE_KILL") == "1":
            return True
        kill_file = Path("data/KILL")
        return kill_file.exists()

settings = Settings()
