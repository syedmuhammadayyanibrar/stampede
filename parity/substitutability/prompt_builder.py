import json
from pathlib import Path
from typing import Dict, List, Any

def generate_prompt_pool() -> List[Dict[str, Any]]:
    archetypes = [
        "code_generation",
        "structured_extraction",
        "summarization",
        "creative_writing",
        "reasoning_math",
        "rag_qa",
        "classification",
        "translation"
    ]
    prompts = []

    for arch in archetypes:
        for pool in ("probe", "holdout"):
            count = 40
            for i in range(1, count + 1):
                pid = f"{arch}_{pool}_{i:03d}"
                is_verifiable = arch in (
                    "code_generation",
                    "structured_extraction",
                    "reasoning_math",
                    "classification",
                    "translation"
                )

                if arch == "code_generation":
                    p_text = f"Write a Python function solve_{pool}_{i}(n: int) -> int that computes the sum of the first n odd squares."
                    meta = {
                        "function_name": f"solve_{pool}_{i}",
                        "test_cases": [
                            {"input": 1, "expected": 1},
                            {"input": 3, "expected": 35},
                            {"input": 5, "expected": 165}
                        ]
                    }
                elif arch == "structured_extraction":
                    p_text = f"Extract customer name, order ID, and total amount in USD from the following text into a JSON object conforming to the schema:\nInvoice #{1000 + i}: Issued to Customer_{pool}_{i} on 2026-08-{i%28 + 1:02d} for total USD {150 + i * 2.5:.2f}."
                    meta = {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "customer_name": {"type": "string"},
                                "order_id": {"type": "string"},
                                "total_usd": {"type": "number"}
                            },
                            "required": ["customer_name", "order_id", "total_usd"]
                        },
                        "expected": {
                            "customer_name": f"Customer_{pool}_{i}",
                            "order_id": f"#{1000 + i}",
                            "total_usd": round(150 + i * 2.5, 2)
                        }
                    }
                elif arch == "summarization":
                    p_text = f"Summarize the executive memorandum on datacenter cooling efficiency in Q3 2026. Emphasize target metrics for cluster {pool}_{i}, specifically power usage effectiveness (PUE) reduction of {10 + (i % 15)}% and operational uptime target of 99.99%."
                    meta = {
                        "rubric": "Evaluates concise capture of PUE reduction metric and uptime guarantee without omitting key cluster identification.",
                        "key_elements": [f"cluster {pool}_{i}", f"{10 + (i % 15)}%", "99.99%"]
                    }
                elif arch == "creative_writing":
                    p_text = f"Draft an announcement for the launch of synthetic compute hedge contracts named Horizon-{pool}-{i}. Include exactly three bullet points detailing forward liquidity, secondary resale options, and collateral mechanics. Do not use the word 'guaranteed'."
                    meta = {
                        "rubric": "Tone must be institutional and clear; exactly three bullet points; strictly forbidden word 'guaranteed' must be absent.",
                        "forbidden_words": ["guaranteed"],
                        "required_bullets": 3
                    }
                elif arch == "reasoning_math":
                    a = 10 + (i * 3)
                    b = 5 + (i * 2)
                    c = 2 + (i % 5)
                    ans = (a * b) - c
                    p_text = f"A server cluster processes {a} batches per hour with {b} tasks per batch. If {c} tasks fail due to transient network drops, what is the net number of successfully processed tasks in one hour? Provide the final numerical answer as an integer."
                    meta = {
                        "expected_value": ans,
                        "operands": [a, b, c]
                    }
                elif arch == "rag_qa":
                    doc = f"Context Document: Touchmark Token Futures (Contract ID TTF-{pool}-{i}) settle in cash against the 7-day TWAP of primary API provider spot pricing. The initial maintenance margin requirement is {15 + (i % 10)}% of notional value."
                    p_text = f"{doc}\nQuestion: What is the settlement mechanism and maintenance margin requirement for contract TTF-{pool}-{i}?"
                    meta = {
                        "expected_settlement": "7-day TWAP cash settlement",
                        "expected_margin": f"{15 + (i % 10)}%"
                    }
                elif arch == "classification":
                    categories = ["LOW_LATENCY_INFERENCE", "BATCH_OFFLINE_TRAINING", "HYBRID_FINE_TUNING", "DEVELOPER_PROTOTYPING"]
                    cat = categories[i % 4]
                    p_text = f"Classify the following compute workload into exactly one category: LOW_LATENCY_INFERENCE, BATCH_OFFLINE_TRAINING, HYBRID_FINE_TUNING, DEVELOPER_PROTOTYPING.\nWorkload description: Request pattern {pool}_{i} requires priority GPU streaming for real-time customer voice agents under 150ms timeout." if cat == "LOW_LATENCY_INFERENCE" else f"Classify the following compute workload into exactly one category: LOW_LATENCY_INFERENCE, BATCH_OFFLINE_TRAINING, HYBRID_FINE_TUNING, DEVELOPER_PROTOTYPING.\nWorkload description: Workload {pool}_{i} executes scheduled nightly data transformations and token embedding recalculations with no strict SLA."
                    effective_cat = "LOW_LATENCY_INFERENCE" if cat == "LOW_LATENCY_INFERENCE" else "BATCH_OFFLINE_TRAINING"
                    meta = {
                        "expected_category": effective_cat,
                        "valid_categories": categories
                    }
                elif arch == "translation":
                    phrases = [
                        ("High-availability inference clusters ensure seamless failover.", "Les clusters d'inférence à haute disponibilité assurent un basculement transparent."),
                        ("Secondary market liquidity tightens during generational releases.", "La liquidité du marché secondaire se resserre lors des lancements générationnels."),
                        ("Forward pricing locks compute discount against spot inflation.", "La tarification à terme verrouille une remise sur le calcul contre l'inflation au comptant."),
                        ("Risk-neutral valuation relies on martingale measure expectations.", "L'évaluation neutre au risque repose sur les espérances de la mesure martingale.")
                    ]
                    src, tgt = phrases[i % len(phrases)]
                    p_text = f"Translate the following financial-technical text to French accurately:\n'{src}'"
                    meta = {
                        "source_text": src,
                        "reference_translation": tgt
                    }

                prompts.append({
                    "id": pid,
                    "archetype": arch,
                    "pool": pool,
                    "prompt": p_text,
                    "verifiable": is_verifiable,
                    "metadata": meta
                })

    return prompts

def build_and_save_prompt_pool(output_path: Path) -> Path:
    data = generate_prompt_pool()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return output_path
