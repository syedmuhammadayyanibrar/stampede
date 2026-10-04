import os
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class PlanEvent:
    description: str
    effective_day_offset: int
    demand_multiplier: float
    confidence: float
    source_quote: str

def extract_demand_plans_deterministic(plan_text: str) -> List[PlanEvent]:
    if not plan_text or not plan_text.strip():
        return []
        
    events = []
    matches = re.finditer(r"([+-]?\d+(?:\.\d+)?)\s*%\s*([a-zA-Z_\-]+(?:\s+[a-zA-Z_\-]+)?)?", plan_text)
    for m in matches:
        raw_num = m.group(1)
        val = float(raw_num)
        start_idx = max(0, m.start() - 25)
        end_idx = min(len(plan_text), m.end() + 25)
        quote = plan_text[start_idx:end_idx].strip()
        
        is_increase = False
        is_decrease = False
        
        if raw_num.startswith("+"):
            is_increase = True
        elif raw_num.startswith("-"):
            is_decrease = True
        else:
            surrounding = plan_text[max(0, m.start() - 30):min(len(plan_text), m.end() + 30)].lower()
            if any(w in surrounding for w in ["increase", "growth", "expand", "surge", "more", "traffic", "load", "volume"]):
                is_increase = True
            elif any(w in surrounding for w in ["cut", "decrease", "drop", "reduce", "reduction", "less", "saving", "efficiency"]):
                is_decrease = True
                
        if is_increase:
            mult = 1.0 + (abs(val) / 100.0)
            events.append(PlanEvent(
                description=f"Planned volume increase (+{abs(val):.0f}%)",
                effective_day_offset=30,
                demand_multiplier=round(mult, 3),
                confidence=0.85,
                source_quote=quote
            ))
        elif is_decrease:
            mult = max(0.20, 1.0 - (abs(val) / 100.0))
            events.append(PlanEvent(
                description=f"Efficiency optimization (-{abs(val):.0f}%)",
                effective_day_offset=60,
                demand_multiplier=round(mult, 3),
                confidence=0.80,
                source_quote=quote
            ))
            
    if not events:
        text_lower = plan_text.lower()
        if "launch" in text_lower or "expand" in text_lower or "release" in text_lower:
            events.append(PlanEvent(
                description="General expansion milestone",
                effective_day_offset=30,
                demand_multiplier=1.25,
                confidence=0.70,
                source_quote=plan_text[:min(80, len(plan_text))].strip()
            ))
            
    return events

def extract_demand_plans(plan_text: str) -> List[PlanEvent]:
    raw_events = extract_demand_plans_deterministic(plan_text)
    
    verified_events = []
    for ev in raw_events:
        if ev.source_quote and ev.source_quote.lower() in plan_text.lower():
            verified_events.append(ev)
        elif any(w.lower() in plan_text.lower() for w in ev.source_quote.split()):
            verified_events.append(ev)
            
    return verified_events
