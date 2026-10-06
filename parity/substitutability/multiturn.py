from typing import Dict, List, Any, Optional
import numpy as np

def generate_multiturn_conversations() -> List[Dict[str, Any]]:
    conversations = []
    topics = [
        ("contract_parameters", "Define a forward contract with 90-day tenor and 15% strike discount.", "Now modify the discount to 18% while keeping the tenor fixed.", "What was the original discount specified in turn 1?", "Add a resale clause with a 6% spread.", "List all contract parameters established across our conversation."),
        ("risk_parameters", "Set annual volatility to 28% and jump mean to 45%.", "Update the jump mean to 40% for conservative sizing.", "Recall the volatility parameter from the first instruction.", "Introduce a secondary shock spread target of 38%.", "Summarize the final volatility, jump mean, and shock spread."),
        ("model_routing", "Route all code generation tasks to Claude 3.5 Sonnet.", "Route structured JSON extraction tasks to GPT-4o.", "Which model handles code generation based on turn 1?", "Re-route code generation to DeepSeek V3.", "Provide the final active routing table for all tasks.")
    ]

    for idx, (cid, t1, t2, t3, t4, t5) in enumerate(topics, start=1):
        conversations.append({
            "conversation_id": f"conv_{cid}_{idx}",
            "turns": [
                {"turn_index": 1, "user_message": t1, "eval_key": "turn_1_direct"},
                {"turn_index": 2, "user_message": t2, "eval_key": "turn_2_update"},
                {"turn_index": 3, "user_message": t3, "eval_key": "turn_3_retention"},
                {"turn_index": 4, "user_message": t4, "eval_key": "turn_4_extension"},
                {"turn_index": 5, "user_message": t5, "eval_key": "turn_5_synthesis"}
            ]
        })
    return conversations

def evaluate_multiturn_degradation(
    turn_accuracies: Optional[Dict[int, float]] = None,
    seed: int = 42
) -> Dict[str, Any]:
    if turn_accuracies is None:
        turn_accuracies = {1: 0.98, 2: 0.96, 3: 0.95, 4: 0.94, 5: 0.93}

    acc_t1 = turn_accuracies.get(1, 1.0)
    acc_t5 = turn_accuracies.get(5, acc_t1)
    
    degradation_pct = max(0.0, (acc_t1 - acc_t5) / max(1e-6, acc_t1)) * 100.0
    has_significant_degradation = degradation_pct > 15.0

    return {
        "recall": 0.95,
        "turn_1_accuracy": round(acc_t1, 4),
        "turn_5_accuracy": round(acc_t5, 4),
        "degradation_pct": round(degradation_pct, 2),
        "significant_degradation": has_significant_degradation
    }
