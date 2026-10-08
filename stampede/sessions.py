import time
import sqlite3
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from stampede.settings import settings
from stampede.types import Notice, StandingNotices

class SessionRecord:
    def __init__(self, session_id: str, byok_key: Optional[str] = None) -> None:
        now = time.time()
        self.session_id: str = session_id
        self.created_at: float = now
        self.last_active_at: float = now
        self.byok_key: Optional[str] = byok_key
        self.inputs: Dict[str, Any] = {
            "usage": None,
            "workload": None,
            "constraints": None,
            "quotes": None
        }
        self.run_records: Dict[str, Any] = {}
        self.session_cache: Dict[str, Any] = {}
        self.draws: Optional[Any] = None
        self.posteriors: Dict[str, Any] = {}
        self.forecast_residuals: Optional[Any] = None
        self.active_run_id: Optional[str] = None
        self.total_spend_usd: float = 0.0
        self.notices: List[Notice] = [
            StandingNotices.OPENROUTER_ROUTING,
            StandingNotices.SIMULATED_EXIT_POOL,
            StandingNotices.ASSUMED_SELLER_PARAMS,
            StandingNotices.THIN_HAZARD_DATA,
            StandingNotices.OPENROUTER_PROXY_PRICES,
            StandingNotices.JUDGE_ERROR_TRANSFER,
            StandingNotices.PARITY_RELATIVE_TO_INCUMBENT,
            StandingNotices.VALUATION_SOURCE
        ]

    def touch(self) -> None:
        self.last_active_at = time.time()

    def get_remaining_budget(self) -> float:
        return max(0.0, settings.session_cap_usd - self.total_spend_usd)

    def is_expired(self) -> bool:
        now = time.time()
        idle_expired = (now - self.last_active_at) > settings.session_idle_ttl_seconds
        hard_cap_expired = (now - self.created_at) > settings.session_hard_cap_seconds
        return idle_expired or hard_cap_expired

class SessionStore:
    def __init__(self, db_path: Path = Path("data/stampede_sessions_meta.db")) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, SessionRecord] = {}
        self._init_sqlite()

    def _init_sqlite(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_meta (
                    session_id TEXT PRIMARY KEY,
                    created_at REAL,
                    total_spend_usd REAL,
                    stage_timings_json TEXT,
                    error_codes_json TEXT
                )
                """
            )
            conn.commit()

    def create_session(self, byok_key: Optional[str] = None) -> SessionRecord:
        self.cleanup_expired()
        session_id = f"ses_{uuid.uuid4().hex[:12]}"
        record = SessionRecord(session_id=session_id, byok_key=byok_key)
        self._sessions[session_id] = record
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO session_meta VALUES (?, ?, ?, ?, ?)",
                (session_id, record.created_at, 0.0, "{}", "[]")
            )
            conn.commit()
        return record

    def get_session(self, session_id: str) -> Optional[SessionRecord]:
        self.cleanup_expired()
        record = self._sessions.get(session_id)
        if record is None:
            return None
        if record.is_expired():
            self.delete_session(session_id)
            return None
        record.touch()
        return record

    def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            rec = self._sessions.pop(session_id)
            rec.session_cache.clear()
            rec.inputs.clear()
            rec.run_records.clear()
            rec.byok_key = None
            rec.draws = None
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM session_meta WHERE session_id = ?", (session_id,))
            conn.commit()
        return True

    def record_meta(self, session_id: str, spend_usd: float, stage_timings: Dict[str, float], errors: List[str]) -> None:
        import json
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE session_meta
                SET total_spend_usd = ?, stage_timings_json = ?, error_codes_json = ?
                WHERE session_id = ?
                """,
                (spend_usd, json.dumps(stage_timings), json.dumps(errors), session_id)
            )
            conn.commit()

    def cleanup_expired(self) -> int:
        expired_ids = [sid for sid, rec in self._sessions.items() if rec.is_expired()]
        for sid in expired_ids:
            self.delete_session(sid)
        return len(expired_ids)

    def count_active_global_runs(self) -> int:
        return sum(1 for rec in self._sessions.values() if rec.active_run_id is not None)

session_store = SessionStore()
