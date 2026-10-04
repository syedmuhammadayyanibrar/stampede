import io
import ast
import tokenize
from pathlib import Path
from typing import List, Tuple

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "data",
    "node_modules",
    "scratch",
    "ai_cache",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    ".egg-info"
}

def get_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent

def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS or part.endswith(".egg-info") for part in path.parts)

def inspect_python_file(path: Path) -> Tuple[List[str], List[str]]:
    source = path.read_text(encoding="utf-8")
    comments = []
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    for tok in tokens:
        if tok.type == tokenize.COMMENT:
            comments.append(f"Line {tok.start[0]}: {tok.string}")

    tree = ast.parse(source, filename=str(path))
    docstrings = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            ds = ast.get_docstring(node, clean=False)
            if ds is not None:
                line_no = getattr(node, "lineno", 1)
                docstrings.append(f"Line {line_no}: {node.__class__.__name__} docstring")

    return comments, docstrings

def inspect_line_based_file(path: Path) -> List[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    violations = []
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            violations.append(f"Line {idx}: {stripped}")
    return violations

def test_no_comments_or_docstrings_in_repo() -> None:
    root = get_repo_root()
    py_violations = {}
    line_violations = {}

    for path in root.rglob("*.py"):
        if is_excluded(path):
            continue
        comments, docstrings = inspect_python_file(path)
        if comments or docstrings:
            py_violations[str(path.relative_to(root))] = {
                "comments": comments,
                "docstrings": docstrings
            }

    for ext in ("*.yaml", "*.yml", "*.toml", "*.json5", "*.sql", "*.sh"):
        for path in root.rglob(ext):
            if is_excluded(path):
                continue
            violations = inspect_line_based_file(path)
            if violations:
                line_violations[str(path.relative_to(root))] = violations

    env_ex = root / ".env.example"
    if env_ex.exists() and not is_excluded(env_ex):
        violations = inspect_line_based_file(env_ex)
        if violations:
            line_violations[str(env_ex.relative_to(root))] = violations

    error_messages = []
    if py_violations:
        for file_path, details in py_violations.items():
            for c in details["comments"]:
                error_messages.append(f"Comment in {file_path} -> {c}")
            for d in details["docstrings"]:
                error_messages.append(f"Docstring in {file_path} -> {d}")

    if line_violations:
        for file_path, violations in line_violations.items():
            for v in violations:
                error_messages.append(f"Comment line in {file_path} -> {v}")

    assert not error_messages, "\n".join(error_messages)
