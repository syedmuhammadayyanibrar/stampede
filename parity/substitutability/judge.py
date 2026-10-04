from typing import Dict, List, Tuple, Optional
import numpy as np

ARCHETYPE_RUBRICS: Dict[str, str] = {
    "code_generation": "Evaluate correctness against function specification, edge cases, error handling, computational efficiency, and adherence to clean type-hinted Python.",
    "structured_extraction": "Evaluate strict schema conformity, absence of hallucinated fields, precision of extracted values, and valid JSON formatting.",
    "summarization": "Evaluate factual accuracy against the source, conciseness, absence of extrinsic hallucinations, and retention of critical operational metrics.",
    "creative_writing": "Evaluate adherence to requested format, constraints (bullet points, forbidden terms), stylistic consistency, and institutional clarity.",
    "reasoning_math": "Evaluate correctness of intermediate reasoning steps, arithmetic fidelity, and exactness of final numerical solution.",
    "rag_qa": "Evaluate faithfulness to provided reference context, completeness of answer, and absence of unsupported claims.",
    "classification": "Evaluate taxonomic accuracy, correctness of category selection, and consistency across boundary cases.",
    "translation": "Evaluate semantic equivalence, preservation of specialized technical terminology, grammatical fluency, and tone."
}

def format_judge_prompt(
    archetype: str,
    prompt_text: str,
    response_a: str,
    response_b: str
) -> str:
    rubric = ARCHETYPE_RUBRICS.get(archetype, "Evaluate overall task correctness and quality.")
    return (
        f"You are an impartial expert evaluator comparing two AI model responses.\n\n"
        f"Workload Archetype: {archetype}\n"
        f"Evaluation Rubric: {rubric}\n\n"
        f"User Task Prompt:\n{prompt_text}\n\n"
        f"Response A:\n{response_a}\n\n"
        f"Response B:\n{response_b}\n\n"
        f"Analyze both responses against the rubric. Conclude with exactly one line:\n"
        f"FINAL_VERDICT: [A|B|TIE]"
    )

def parse_judge_verdict(raw_output: str) -> str:
    lines = raw_output.strip().splitlines()
    for line in reversed(lines):
        upper = line.strip().upper()
        if "FINAL_VERDICT:" in upper:
            v = upper.split("FINAL_VERDICT:")[1].strip()
            if "A" in v and "B" not in v:
                return "A"
            elif "B" in v and "A" not in v:
                return "B"
            elif "TIE" in v:
                return "TIE"
    if "RESPONSE A IS BETTER" in raw_output.upper():
        return "A"
    elif "RESPONSE B IS BETTER" in raw_output.upper():
        return "B"
    return "TIE"

def compute_flip_rate(
    verdicts_forward: List[str],
    verdicts_backward: List[str]
) -> float:
    if not verdicts_forward or len(verdicts_forward) != len(verdicts_backward):
        return 0.0

    flipped_count = 0
    decisive_pairs = 0

    for vf, vb in zip(verdicts_forward, verdicts_backward):
        if vf in ("A", "B") and vb in ("A", "B"):
            decisive_pairs += 1
            if (vf == "A" and vb == "A") or (vf == "B" and vb == "B"):
                flipped_count += 1

    if decisive_pairs == 0:
        return 0.0
    return float(flipped_count / decisive_pairs)

def compute_cohens_kappa(
    rater1_labels: List[int],
    rater2_labels: List[int]
) -> float:
    if not rater1_labels or len(rater1_labels) != len(rater2_labels):
        return 0.0

    n = len(rater1_labels)
    arr1 = np.array(rater1_labels)
    arr2 = np.array(rater2_labels)

    categories = np.unique(np.concatenate([arr1, arr2]))
    if len(categories) <= 1:
        return 1.0

    observed_agreement = float(np.mean(arr1 == arr2))

    expected_agreement = 0.0
    for cat in categories:
        p1 = float(np.mean(arr1 == cat))
        p2 = float(np.mean(arr2 == cat))
        expected_agreement += p1 * p2

    if expected_agreement >= 1.0:
        return 1.0

    kappa = (observed_agreement - expected_agreement) / (1.0 - expected_agreement)
    return float(kappa)

def get_eligible_judges(
    incumbent: str,
    candidate: str,
    candidate_judges: Optional[List[str]] = None
) -> List[str]:
    judges = candidate_judges or [
        "openai/gpt-4o",
        "anthropic/claude-3.5-sonnet",
        "google/gemini-2.5-pro",
        "deepseek/deepseek-chat"
    ]
    def get_family(name: str) -> str:
        lower = name.lower()
        if "gpt" in lower or "openai" in lower:
            return "openai"
        elif "claude" in lower or "anthropic" in lower:
            return "anthropic"
        elif "gemini" in lower or "google" in lower:
            return "google"
        elif "deepseek" in lower:
            return "deepseek"
        return name

    inc_fam = get_family(incumbent)
    cand_fam = get_family(candidate)

    return [j for j in judges if get_family(j) not in (inc_fam, cand_fam)]
