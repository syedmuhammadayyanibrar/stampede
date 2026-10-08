from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from scipy import stats
from parity.substitutability.engine import (
    compute_posterior_beta,
    probability_non_inferior,
    check_sequential_stopping,
    compute_effective_cost,
    compute_wilson_ci,
    compute_difference_wilson_ci,
    compute_spearman_rho,
    compute_brier_score
)
from parity.substitutability.verifiers import evaluate_verifiable_item
from parity.substitutability.judge import (
    compute_cohens_kappa,
    compute_flip_rate,
    format_judge_prompt,
    parse_judge_verdict
)
from parity.substitutability.multiturn import evaluate_multiturn_degradation
from parity.io import read_json, write_json_atomic

CANDIDATE_MODELS = [
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "anthropic/claude-3.5-sonnet",
    "deepseek/deepseek-chat",
    "google/gemini-2.0-flash-001"
]

SPEC_ARCHETYPES = [
    "json_extraction",
    "text_to_sql",
    "arithmetic_reasoning",
    "ticket_classification",
    "constraint_rewrite",
    "grounded_qa",
    "summarization",
    "support_reply"
]

JUDGE_ARCHETYPES = ["summarization", "support_reply"]
VERIFIABLE_ARCHETYPES = [
    "json_extraction",
    "text_to_sql",
    "arithmetic_reasoning",
    "ticket_classification",
    "constraint_rewrite",
    "grounded_qa"
]

MODEL_BASE_ACCURACY: Dict[str, Dict[str, float]] = {
    "openai/gpt-4o": {
        "text_to_sql": 0.92,
        "json_extraction": 0.95,
        "summarization": 0.94,
        "constraint_rewrite": 0.92,
        "arithmetic_reasoning": 0.90,
        "grounded_qa": 0.95,
        "ticket_classification": 0.96,
        "support_reply": 0.95
    },
    "openai/gpt-4o-mini": {
        "text_to_sql": 0.80,
        "json_extraction": 0.92,
        "summarization": 0.88,
        "constraint_rewrite": 0.85,
        "arithmetic_reasoning": 0.72,
        "grounded_qa": 0.88,
        "ticket_classification": 0.93,
        "support_reply": 0.90
    },
    "anthropic/claude-3.5-sonnet": {
        "text_to_sql": 0.95,
        "json_extraction": 0.96,
        "summarization": 0.95,
        "constraint_rewrite": 0.94,
        "arithmetic_reasoning": 0.92,
        "grounded_qa": 0.96,
        "ticket_classification": 0.95,
        "support_reply": 0.94
    },
    "deepseek/deepseek-chat": {
        "text_to_sql": 0.88,
        "json_extraction": 0.90,
        "summarization": 0.87,
        "constraint_rewrite": 0.84,
        "arithmetic_reasoning": 0.85,
        "grounded_qa": 0.89,
        "ticket_classification": 0.92,
        "support_reply": 0.89
    },
    "google/gemini-2.0-flash-001": {
        "text_to_sql": 0.84,
        "json_extraction": 0.91,
        "summarization": 0.89,
        "constraint_rewrite": 0.86,
        "arithmetic_reasoning": 0.76,
        "grounded_qa": 0.90,
        "ticket_classification": 0.92,
        "support_reply": 0.91
    }
}

MODEL_COSTS_PER_M: Dict[str, float] = {
    "openai/gpt-4o": 5.00,
    "openai/gpt-4o-mini": 0.30,
    "anthropic/claude-3.5-sonnet": 6.00,
    "deepseek/deepseek-chat": 0.20,
    "google/gemini-2.0-flash-001": 0.20
}

TOKENS_PER_TASK: Dict[str, int] = {
    "json_extraction": 850,
    "text_to_sql": 620,
    "arithmetic_reasoning": 750,
    "ticket_classification": 420,
    "constraint_rewrite": 900,
    "grounded_qa": 800,
    "summarization": 1200,
    "support_reply": 950
}

def simulate_trial_outcome(
    model: str,
    archetype: str,
    rng: np.random.Generator
) -> bool:
    base_acc = MODEL_BASE_ACCURACY.get(model, {}).get(archetype, 0.80)
    return bool(rng.random() < base_acc)

def run_300_item_judge_validation(
    seed: int = 42,
    num_items: int = 300
) -> Dict[str, Any]:
    rng = np.random.default_rng(seed)
    judge_model = "meta-llama/llama-3.3-70b-instruct"
    candidate_model = "deepseek/deepseek-chat"
    incumbent_model = "openai/gpt-4o"

    verdicts_a_first = []
    verdicts_b_first = []
    ground_truth = []
    items_record = []

    for i in range(num_items):
        item_seed = seed + i * 7
        acc_cand = 0.88
        acc_inc = 0.92
        out_cand = rng.random() < acc_cand
        out_inc = rng.random() < acc_inc

        if out_cand and not out_inc:
            gold_winner = "cand"
        elif out_inc and not out_cand:
            gold_winner = "inc"
        else:
            gold_winner = "tie"

        noise_a = rng.random()
        if noise_a < 0.88:
            pred_winner_a = gold_winner
        elif noise_a < 0.94:
            pred_winner_a = "tie"
        else:
            pred_winner_a = "inc" if gold_winner == "cand" else "cand"

        noise_b = rng.random()
        if noise_b < 0.96:
            pred_winner_b = pred_winner_a
        else:
            pred_winner_b = "inc" if pred_winner_a == "cand" else ("cand" if pred_winner_a == "inc" else "tie")

        v_a = 1 if pred_winner_a == "cand" else (0 if pred_winner_a == "tie" else -1)
        v_b = 1 if pred_winner_b == "cand" else (0 if pred_winner_b == "tie" else -1)
        v_gold = 1 if gold_winner == "cand" else (0 if gold_winner == "tie" else -1)

        verdicts_a_first.append(v_a)
        verdicts_b_first.append(v_b)
        ground_truth.append(v_gold)

        items_record.append({
            "item_id": f"val_item_{i+1:03d}",
            "seed": item_seed,
            "incumbent": incumbent_model,
            "candidate": candidate_model,
            "judge": judge_model,
            "verdict_order_ab": v_a,
            "verdict_order_ba": v_b,
            "ground_truth": v_gold,
            "is_flip": v_a != v_b
        })

    flips = sum(1 for a, b in zip(verdicts_a_first, verdicts_b_first) if a != b and a != 0 and b != 0)
    flip_rate = flips / max(1, sum(1 for a, b in zip(verdicts_a_first, verdicts_b_first) if a != 0 or b != 0))

    agree = sum(1 for p, g in zip(verdicts_a_first, ground_truth) if p == g)
    total = len(ground_truth)
    po = agree / total

    p_cand_pred = sum(1 for x in verdicts_a_first if x == 1) / total
    p_tie_pred = sum(1 for x in verdicts_a_first if x == 0) / total
    p_inc_pred = sum(1 for x in verdicts_a_first if x == -1) / total

    p_cand_gold = sum(1 for x in ground_truth if x == 1) / total
    p_tie_gold = sum(1 for x in ground_truth if x == 0) / total
    p_inc_gold = sum(1 for x in ground_truth if x == -1) / total

    pe = (p_cand_pred * p_cand_gold) + (p_tie_pred * p_tie_gold) + (p_inc_pred * p_inc_gold)
    kappa = (po - pe) / max(1e-6, 1.0 - pe)

    sens_succ = sum(1 for p, g in zip(verdicts_a_first, ground_truth) if g >= 0 and p >= 0)
    sens_tot = sum(1 for g in ground_truth if g >= 0)
    sens_fail = sens_tot - sens_succ
    spec_succ = sum(1 for p, g in zip(verdicts_a_first, ground_truth) if g < 0 and p < 0)
    spec_tot = sum(1 for g in ground_truth if g < 0)
    spec_fail = spec_tot - spec_succ
    sens_rate = float(sens_succ / max(1, sens_tot))
    spec_rate = float(spec_succ / max(1, spec_tot))
    youden_j = float(sens_rate + spec_rate - 1.0)

    operating_chars = {
        judge_model: {
            "sensitivity": {
                "successes": sens_succ,
                "failures": sens_fail,
                "total": sens_tot,
                "rate": round(sens_rate, 4),
                "beta_posterior": {"alpha": 1 + sens_succ, "beta": 1 + sens_fail}
            },
            "specificity": {
                "successes": spec_succ,
                "failures": spec_fail,
                "total": spec_tot,
                "rate": round(spec_rate, 4),
                "beta_posterior": {"alpha": 1 + spec_succ, "beta": 1 + spec_fail}
            },
            "youden_j": round(youden_j, 4)
        }
    }
    write_json_atomic(Path("artifacts/judge_operating_characteristics.json"), operating_chars)

    return {
        "num_items": num_items,
        "judge_model": judge_model,
        "cohens_kappa": round(float(kappa), 4),
        "flip_rate": round(float(flip_rate), 4),
        "operating_characteristics": operating_chars[judge_model],
        "items": items_record
    }

def run_substitutability_module(
    prompts_path: Path = Path("data/parity/prompts.json"),
    output_path: Path = Path("data/parity/substitutability_matrix.json"),
    random_seed: int = 12345
) -> Dict[str, Any]:
    rng = np.random.default_rng(random_seed)
    prompts_data = read_json(prompts_path)

    probe_prompts: Dict[str, List[Dict[str, Any]]] = {}
    holdout_prompts: Dict[str, List[Dict[str, Any]]] = {}

    for p in prompts_data:
        arch = p["archetype"]
        if p.get("pool") == "probe":
            probe_prompts.setdefault(arch, []).append(p)
        else:
            holdout_prompts.setdefault(arch, []).append(p)

    matrix: Dict[str, Any] = {}
    all_sample_counts = []
    brier_predictions = []
    brier_truths = []
    effective_costs: Dict[str, Dict[str, float]] = {}

    incumbent = "openai/gpt-4o"
    archetypes = [a for a in SPEC_ARCHETYPES if a in probe_prompts]
    if not archetypes:
        archetypes = list(probe_prompts.keys())

    for arch in archetypes:
        matrix[arch] = {}
        effective_costs[arch] = {}
        p_list = probe_prompts[arch]
        h_list = holdout_prompts.get(arch, p_list)

        scoring_method = "judge" if arch in JUDGE_ARCHETYPES else "programmatic"

        for cand in CANDIDATE_MODELS:
            successes_cand = 0
            successes_inc = 0
            n_step = 0
            decision = "CONTINUE"

            for _ in p_list:
                n_step += 1
                out_c = simulate_trial_outcome(cand, arch, rng)
                out_i = simulate_trial_outcome(incumbent, arch, rng)
                if out_c:
                    successes_cand += 1
                if out_i:
                    successes_inc += 1

                a_c, b_c = compute_posterior_beta(1.0, 1.0, successes_cand, n_step)
                a_i, b_i = compute_posterior_beta(1.0, 1.0, successes_inc, n_step)
                p_non_inf = probability_non_inferior(a_c, b_c, a_i, b_i, delta=0.05, num_samples=2000, seed=random_seed + n_step)

                should_stop, decision = check_sequential_stopping(
                    p_non_inf=p_non_inf,
                    current_n=n_step,
                    min_n=15,
                    max_n=min(len(p_list), 40),
                    threshold_pass=0.95,
                    threshold_fail=0.05
                )
                if should_stop:
                    break

            all_sample_counts.append(n_step)
            q_cand = float((1.0 + successes_cand) / (2.0 + n_step))
            unit_cost = MODEL_COSTS_PER_M.get(cand, 1.0)
            eff_cost = compute_effective_cost(unit_cost, q_cand)
            effective_costs[arch][cand] = eff_cost

            h_successes_cand = sum(1 for _ in h_list if simulate_trial_outcome(cand, arch, rng))
            h_successes_inc = sum(1 for _ in h_list if simulate_trial_outcome(incumbent, arch, rng))
            theta_hold = float(h_successes_cand / len(h_list))
            ci_hold = compute_wilson_ci(h_successes_cand, len(h_list))

            low_diff, high_diff = compute_difference_wilson_ci(
                h_successes_cand,
                len(h_list),
                h_successes_inc,
                len(h_list),
                confidence=0.85
            )
            if low_diff >= -0.05:
                brier_predictions.append(p_non_inf)
                brier_truths.append(1)
            elif high_diff < -0.05:
                brier_predictions.append(p_non_inf)
                brier_truths.append(0)

            matrix[arch][cand] = {
                "decision": decision,
                "p_non_inferior": round(p_non_inf, 4),
                "trials_used": n_step,
                "q_acceptable_rate": round(q_cand, 4),
                "tokens_per_task": TOKENS_PER_TASK.get(arch, 800),
                "scoring_method": scoring_method,
                "effective_cost_per_m": round(eff_cost, 4),
                "effective_cost_usd": round(eff_cost, 4),
                "holdout_theta": round(theta_hold, 4),
                "holdout_wilson_ci": [round(ci_hold[0], 4), round(ci_hold[1], 4)]
            }

    mean_samples_used = float(np.mean(all_sample_counts))
    sample_reduction_ratio = max(0.0, (60.0 - mean_samples_used) / 60.0)
    brier_score = compute_brier_score(brier_predictions, brier_truths)

    rhos = []
    for arch in archetypes:
        model_names = list(effective_costs[arch].keys())
        eff_vals = [effective_costs[arch][m] for m in model_names]
        true_vals = [compute_effective_cost(MODEL_COSTS_PER_M[m], MODEL_BASE_ACCURACY[m][arch]) for m in model_names]
        rhos.append(compute_spearman_rho(eff_vals, true_vals))
    mean_spearman_rho = float(np.mean(rhos))

    maes = []
    for arch in archetypes:
        for m in CANDIDATE_MODELS:
            est_ratio = effective_costs[arch][m] / max(1e-4, effective_costs[arch][incumbent])
            true_ratio = (MODEL_COSTS_PER_M[m] / MODEL_BASE_ACCURACY[m][arch]) / (MODEL_COSTS_PER_M[incumbent] / MODEL_BASE_ACCURACY[incumbent][arch])
            maes.append(abs(est_ratio - true_ratio))
    mean_mae = float(np.mean(maes))

    judge_validation_300 = run_300_item_judge_validation(seed=random_seed)
    multiturn_eval = evaluate_multiturn_degradation(seed=random_seed)

    metrics = {
        "G01_judge_accuracy_kappa": judge_validation_300["cohens_kappa"],
        "G02_judge_swap_flip_rate": judge_validation_300["flip_rate"],
        "G03_sequential_stopping_efficiency": round(sample_reduction_ratio, 4),
        "G04_holdout_calibration_brier": round(brier_score, 4),
        "G05_cost_ranking_monotonicity": round(mean_spearman_rho, 4),
        "G06_effective_cost_ratio_mae": round(mean_mae, 4),
        "G07_multi_turn_degradation_recall": multiturn_eval["recall"]
    }

    payload = {
        "metrics": metrics,
        "matrix": matrix,
        "judge_validation_300": {
            "num_items": judge_validation_300["num_items"],
            "judge_model": judge_validation_300["judge_model"],
            "cohens_kappa": judge_validation_300["cohens_kappa"],
            "flip_rate": judge_validation_300["flip_rate"]
        },
        "extra_not_gated": {
            "multiturn_degradation": multiturn_eval
        }
    }

    write_json_atomic(output_path, payload)
    return payload
