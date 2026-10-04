import os
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, List, Any

def get_openrouter_api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY")
    if key:
        return key.strip()
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""

def fetch_rankings_daily(start_date: str, end_date: str, cache_dir: str = "data/openrouter_cache") -> List[Dict[str, Any]]:
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"rankings_{start_date}_{end_date}.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    key = get_openrouter_api_key()
    headers = {
        "Authorization": f"Bearer {key}",
        "User-Agent": "TouchmarkRiskEngine/2.0 (CC BY 4.0 OpenRouter Research)"
    }
    
    d_start = datetime.strptime(start_date, "%Y-%m-%d")
    d_end = datetime.strptime(end_date, "%Y-%m-%d")
    
    all_data = []
    curr = d_start
    while curr <= d_end:
        chunk_end = min(curr + timedelta(days=10), d_end)
        s_str = curr.strftime("%Y-%m-%d")
        e_str = chunk_end.strftime("%Y-%m-%d")
        
        chunk_cache = os.path.join(cache_dir, f"chunk_{s_str}_{e_str}.json")
        if os.path.exists(chunk_cache):
            with open(chunk_cache, "r", encoding="utf-8") as f:
                chunk_data = json.load(f)
        else:
            url = f"https://openrouter.ai/api/v1/datasets/rankings-daily?start_date={s_str}&end_date={e_str}"
            req = urllib.request.Request(url, headers=headers)
            chunk_data = []
            for attempt in range(4):
                try:
                    time.sleep(0.5)
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        payload = json.loads(resp.read().decode("utf-8"))
                        chunk_data = payload.get("data", [])
                        with open(chunk_cache, "w", encoding="utf-8") as f:
                            json.dump(chunk_data, f, indent=2)
                        break
                except Exception:
                    time.sleep(1.5 * (attempt + 1))
        
        all_data.extend(chunk_data)
        curr = chunk_end + timedelta(days=1)
    
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2)
    
    return all_data
