import json
import time
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class RunEvent(BaseModel):
    seq: int
    event_type: str
    stage: str
    timestamp: float
    payload: Dict[str, Any]

    def to_sse_format(self) -> str:
        data_str = json.dumps({
            "seq": self.seq,
            "event_type": self.event_type,
            "stage": self.stage,
            "timestamp": self.timestamp,
            "payload": self.payload
        })
        return f"id: {self.seq}\nevent: {self.event_type}\ndata: {data_str}\n\n"

class EventLog:
    def __init__(self) -> None:
        self.events: List[RunEvent] = []
        self._next_seq: int = 1

    def emit(self, event_type: str, stage: str, payload: Dict[str, Any]) -> RunEvent:
        event = RunEvent(
            seq=self._next_seq,
            event_type=event_type,
            stage=stage,
            timestamp=round(time.time(), 4),
            payload=payload
        )
        self.events.append(event)
        self._next_seq += 1
        return event

    def get_events_since(self, last_event_id: Optional[int] = None) -> List[RunEvent]:
        if last_event_id is None:
            return list(self.events)
        return [e for e in self.events if e.seq > last_event_id]
