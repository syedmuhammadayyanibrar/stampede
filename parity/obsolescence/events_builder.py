import json
from pathlib import Path
from typing import Dict, List, Any

def get_historical_event_records() -> List[Dict[str, Any]]:
    return [
        {
            "id": "openai_gpt4_launch",
            "provider": "OpenAI",
            "model_name": "gpt-4-0314",
            "event_type": "release",
            "date": "2023-03-14",
            "price_input_per_m": 30.00,
            "price_output_per_m": 60.00,
            "successor": "gpt-4-0613",
            "source_verified": True
        },
        {
            "id": "openai_gpt4_turbo_launch",
            "provider": "OpenAI",
            "model_name": "gpt-4-1106-preview",
            "event_type": "release",
            "date": "2023-11-06",
            "price_input_per_m": 10.00,
            "price_output_per_m": 30.00,
            "successor": "gpt-4-0125-preview",
            "source_verified": True
        },
        {
            "id": "openai_gpt4o_launch",
            "provider": "OpenAI",
            "model_name": "gpt-4o-2024-05-13",
            "event_type": "release",
            "date": "2024-05-13",
            "price_input_per_m": 5.00,
            "price_output_per_m": 15.00,
            "successor": "gpt-4o-mini",
            "source_verified": True
        },
        {
            "id": "openai_gpt4o_mini_launch",
            "provider": "OpenAI",
            "model_name": "gpt-4o-mini-2024-07-18",
            "event_type": "release",
            "date": "2024-07-18",
            "price_input_per_m": 0.15,
            "price_output_per_m": 0.60,
            "successor": None,
            "source_verified": True
        },
        {
            "id": "openai_gpt4o_price_cut",
            "provider": "OpenAI",
            "model_name": "gpt-4o",
            "event_type": "price_cut",
            "date": "2024-08-06",
            "price_input_per_m": 2.50,
            "price_output_per_m": 10.00,
            "successor": None,
            "source_verified": True
        },
        {
            "id": "anthropic_claude2_launch",
            "provider": "Anthropic",
            "model_name": "claude-2.0",
            "event_type": "release",
            "date": "2023-07-11",
            "price_input_per_m": 8.00,
            "price_output_per_m": 24.00,
            "successor": "claude-2.1",
            "source_verified": True
        },
        {
            "id": "anthropic_claude3_opus_launch",
            "provider": "Anthropic",
            "model_name": "claude-3-opus-20240229",
            "event_type": "release",
            "date": "2024-03-04",
            "price_input_per_m": 15.00,
            "price_output_per_m": 75.00,
            "successor": "claude-3.5-sonnet",
            "source_verified": True
        },
        {
            "id": "anthropic_claude35_sonnet_launch",
            "provider": "Anthropic",
            "model_name": "claude-3-5-sonnet-20240620",
            "event_type": "release",
            "date": "2024-06-20",
            "price_input_per_m": 3.00,
            "price_output_per_m": 15.00,
            "successor": "claude-3-5-sonnet-20241022",
            "source_verified": True
        },
        {
            "id": "anthropic_claude37_sonnet_launch",
            "provider": "Anthropic",
            "model_name": "claude-3-7-sonnet-20250219",
            "event_type": "release",
            "date": "2025-02-24",
            "price_input_per_m": 3.00,
            "price_output_per_m": 15.00,
            "successor": None,
            "source_verified": True
        },
        {
            "id": "anthropic_claude2_deprecation",
            "provider": "Anthropic",
            "model_name": "claude-2.0",
            "event_type": "deprecation_notice",
            "date": "2024-09-15",
            "price_input_per_m": 8.00,
            "price_output_per_m": 24.00,
            "successor": "claude-3-haiku",
            "source_verified": True
        },
        {
            "id": "google_gemini_10_pro_launch",
            "provider": "Google",
            "model_name": "gemini-1.0-pro",
            "event_type": "release",
            "date": "2023-12-13",
            "price_input_per_m": 0.50,
            "price_output_per_m": 1.50,
            "successor": "gemini-1.5-pro",
            "source_verified": True
        },
        {
            "id": "google_gemini_15_pro_launch",
            "provider": "Google",
            "model_name": "gemini-1.5-pro-001",
            "event_type": "release",
            "date": "2024-02-15",
            "price_input_per_m": 3.50,
            "price_output_per_m": 10.50,
            "successor": "gemini-1.5-flash",
            "source_verified": True
        },
        {
            "id": "google_gemini_15_flash_launch",
            "provider": "Google",
            "model_name": "gemini-1.5-flash-001",
            "event_type": "release",
            "date": "2024-05-14",
            "price_input_per_m": 0.35,
            "price_output_per_m": 1.05,
            "successor": "gemini-2.0-flash",
            "source_verified": True
        },
        {
            "id": "google_gemini_20_flash_launch",
            "provider": "Google",
            "model_name": "gemini-2.0-flash-001",
            "event_type": "release",
            "date": "2025-02-05",
            "price_input_per_m": 0.10,
            "price_output_per_m": 0.40,
            "successor": None,
            "source_verified": True
        },
        {
            "id": "deepseek_v2_launch",
            "provider": "DeepSeek",
            "model_name": "deepseek-v2",
            "event_type": "release",
            "date": "2024-05-07",
            "price_input_per_m": 0.14,
            "price_output_per_m": 0.28,
            "successor": "deepseek-v2.5",
            "source_verified": True
        },
        {
            "id": "deepseek_v3_launch",
            "provider": "DeepSeek",
            "model_name": "deepseek-chat-v3-0324",
            "event_type": "release",
            "date": "2024-12-26",
            "price_input_per_m": 0.14,
            "price_output_per_m": 0.28,
            "successor": "deepseek-r1",
            "source_verified": True
        },
        {
            "id": "deepseek_r1_launch",
            "provider": "DeepSeek",
            "model_name": "deepseek-r1",
            "event_type": "release",
            "date": "2025-01-20",
            "price_input_per_m": 0.55,
            "price_output_per_m": 2.19,
            "successor": None,
            "source_verified": True
        },
        {
            "id": "meta_llama3_70b_launch",
            "provider": "Meta",
            "model_name": "meta-llama/llama-3-70b-instruct",
            "event_type": "release",
            "date": "2024-04-18",
            "price_input_per_m": 0.90,
            "price_output_per_m": 0.90,
            "successor": "meta-llama/llama-3.1-70b-instruct",
            "source_verified": True
        },
        {
            "id": "meta_llama31_70b_launch",
            "provider": "Meta",
            "model_name": "meta-llama/llama-3.1-70b-instruct",
            "event_type": "release",
            "date": "2024-07-23",
            "price_input_per_m": 0.88,
            "price_output_per_m": 0.88,
            "successor": "meta-llama/llama-3.3-70b-instruct",
            "source_verified": True
        },
        {
            "id": "meta_llama33_70b_launch",
            "provider": "Meta",
            "model_name": "meta-llama/llama-3.3-70b-instruct",
            "event_type": "release",
            "date": "2024-12-06",
            "price_input_per_m": 0.70,
            "price_output_per_m": 0.70,
            "successor": None,
            "source_verified": True
        },
        {
            "id": "mistral_large_launch",
            "provider": "Mistral",
            "model_name": "mistral-large-2402",
            "event_type": "release",
            "date": "2024-02-26",
            "price_input_per_m": 8.00,
            "price_output_per_m": 24.00,
            "successor": "mistral-large-2407",
            "source_verified": True
        },
        {
            "id": "mistral_large2_launch",
            "provider": "Mistral",
            "model_name": "mistral-large-2407",
            "event_type": "release",
            "date": "2024-07-24",
            "price_input_per_m": 2.00,
            "price_output_per_m": 6.00,
            "successor": None,
            "source_verified": True
        },
        {
            "id": "mistral_medium_shutdown",
            "provider": "Mistral",
            "model_name": "mistral-medium-2312",
            "event_type": "shutdown",
            "date": "2024-06-01",
            "price_input_per_m": 2.70,
            "price_output_per_m": 8.10,
            "successor": "mistral-small",
            "source_verified": True
        }
    ]

def build_and_save_historical_events(output_path: Path) -> Path:
    events = get_historical_event_records()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)
    return output_path
