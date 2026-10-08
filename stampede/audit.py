import ast
from pathlib import Path
from typing import Dict, List, Any

def detect_gateway_calls_in_node(node: ast.AST) -> List[str]:
    calls = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            if isinstance(sub.func, ast.Attribute):
                val_name = ""
                if isinstance(sub.func.value, ast.Name):
                    val_name = sub.func.value.id
                elif isinstance(sub.func.value, ast.Attribute):
                    val_name = sub.func.value.attr
                if "gateway" in val_name.lower():
                    calls.append(f"{val_name}.{sub.func.attr}")
                elif sub.func.attr in ("complete", "call", "generate", "chat", "call_model"):
                    calls.append(sub.func.attr)
            elif isinstance(sub.func, ast.Name):
                if sub.func.id in ("call_model", "LLMGateway", "FakeGateway"):
                    calls.append(sub.func.id)
    return calls

def inspect_python_file(file_path: Path) -> List[Dict[str, Any]]:
    results = []
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            calls = detect_gateway_calls_in_node(node)
            results.append({
                "file": str(file_path.name),
                "path": str(file_path),
                "component": node.name,
                "kind": "function",
                "calls_gateway": len(calls) > 0,
                "call_functions": calls,
                "classification": "LLM" if len(calls) > 0 else "DETERMINISTIC"
            })
        elif isinstance(node, ast.ClassDef):
            class_calls = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_calls = detect_gateway_calls_in_node(item)
                    if method_calls:
                        class_calls.extend(method_calls)
                        results.append({
                            "file": str(file_path.name),
                            "path": str(file_path),
                            "component": f"{node.name}.{item.name}",
                            "kind": "method",
                            "calls_gateway": True,
                            "call_functions": method_calls,
                            "classification": "LLM"
                        })
            if not class_calls:
                results.append({
                    "file": str(file_path.name),
                    "path": str(file_path),
                    "component": node.name,
                    "kind": "class",
                    "calls_gateway": False,
                    "call_functions": [],
                    "classification": "DETERMINISTIC"
                })
    return results

def audit_components(root_dir: Path = Path(".")) -> List[Dict[str, Any]]:
    targets = []
    stampede_dir = root_dir / "stampede"
    if stampede_dir.exists():
        targets.extend(stampede_dir.rglob("*.py"))
    parity_agent_dir = root_dir / "parity" / "agent"
    if parity_agent_dir.exists():
        targets.extend(parity_agent_dir.rglob("*.py"))
    sub_judge = root_dir / "parity" / "substitution" / "judge.py"
    if sub_judge.exists():
        targets.append(sub_judge)
    sub2_judge = root_dir / "parity" / "substitutability" / "judge.py"
    if sub2_judge.exists():
        targets.append(sub2_judge)

    audit_records = []
    for t in sorted(set(targets)):
        if "__pycache__" in t.parts:
            continue
        audit_records.extend(inspect_python_file(t))
    return audit_records

def main() -> None:
    records = audit_components()
    print(f"{'Component':<40} {'Kind':<10} {'Classification':<15} {'Calls'}")
    print("-" * 80)
    for r in records:
        calls_str = ", ".join(r["call_functions"]) if r["call_functions"] else "-"
        print(f"{r['component']:<40} {r['kind']:<10} {r['classification']:<15} {calls_str}")

if __name__ == "__main__":
    main()
