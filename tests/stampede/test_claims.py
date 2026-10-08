import re
from pathlib import Path

BANNED_PHRASES = [
    "zero-hallucination",
    "hallucination-free",
    "100% recovery",
    "guaranteed",
    "graph-free",
    "100% envy-free"
]

def test_no_banned_phrases_in_docs_and_readme():
    root = Path(__file__).resolve().parent.parent.parent
    violations = []

    for path in [root / "README.md", *(root / "docs").glob("*.md")]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in BANNED_PHRASES:
            if phrase.lower() in text.lower():
                violations.append(f"Banned phrase '{phrase}' found in {path.name}")

    assert not violations, "\n".join(violations)

def test_no_banned_phrases_in_web_ui():
    root = Path(__file__).resolve().parent.parent.parent
    web_dir = root / "web"
    violations = []

    if web_dir.exists():
        for path in web_dir.rglob("*"):
            if path.is_file() and path.suffix in (".html", ".js", ".css"):
                text = path.read_text(encoding="utf-8", errors="ignore")
                for phrase in BANNED_PHRASES:
                    if phrase.lower() in text.lower():
                        violations.append(f"Banned phrase '{phrase}' found in web file {path.name}")
                if "parity" in text.lower():
                    clean_text = re.sub(r"/api/[a-zA-Z0-9_/]+", "", text)
                    if "parity" in clean_text.lower():
                        violations.append(f"Forbidden term 'Parity' found in web UI file {path.name}")

    assert not violations, "\n".join(violations)

def test_no_parity_in_readme_headlines():
    root = Path(__file__).resolve().parent.parent.parent
    readme = root / "README.md"
    violations = []
    if readme.exists():
        for idx, line in enumerate(readme.read_text(encoding="utf-8").splitlines(), start=1):
            if line.strip().startswith("#"):
                if "parity" in line.lower():
                    violations.append(f"Headline on line {idx} contains 'Parity': {line}")
    assert not violations, "\n".join(violations)

def test_no_banned_claims_in_evals_and_reports():
    root = Path(__file__).resolve().parent.parent.parent
    violations = []
    scan_paths = [
        *(root / "evals").glob("*.md"),
        *(root / "evals").glob("*.yaml"),
        *(root / "reports").glob("*.md"),
        *(root / "reports").glob("*.json")
    ]
    for path in scan_paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for phrase in BANNED_PHRASES:
            if phrase.lower() in text.lower():
                violations.append(f"Banned phrase '{phrase}' found in {path.name}")
        for line in text.splitlines():
            if line.strip().startswith("#") and "hallucination" in line.lower():
                violations.append(f"Heading in {path.name} contains 'hallucination': {line}")
            if "| **Hallucination" in line:
                violations.append(f"Table row heading in {path.name} contains 'Hallucination': {line}")

    assert not violations, "\n".join(violations)
