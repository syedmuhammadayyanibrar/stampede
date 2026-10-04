import sys
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import yaml
from rich.console import Console
from rich.table import Table
from parity.io import write_json_atomic, write_text_atomic

def verify_thresholds_lock(
    yaml_path: Path = Path("evals/thresholds_parity.yaml"),
    lock_path: Path = Path("evals/thresholds_parity.lock")
) -> bool:
    if not yaml_path.exists() or not lock_path.exists():
        return False
    current_bytes = yaml_path.read_bytes()
    expected_digest = lock_path.read_text(encoding="utf-8").strip()
    actual_digest = hashlib.sha256(current_bytes).hexdigest()
    return actual_digest == expected_digest

def build_gate_row(
    gate_id: str,
    spec: Dict[str, Any],
    observed_val: float,
    status: str,
    ci: Optional[Tuple[float, float]] = None
) -> Dict[str, Any]:
    return {
        "gate_id": gate_id,
        "name": spec.get("name", ""),
        "metric": spec.get("metric", ""),
        "target_direction": spec.get("target_direction", "ge"),
        "threshold": spec.get("threshold", 0.0),
        "unit": spec.get("unit", ""),
        "observed_value": round(observed_val, 4),
        "status": status,
        "ci_95": [round(ci[0], 4), round(ci[1], 4)] if ci else None
    }

def print_evaluation_summary(results: List[Dict[str, Any]], console: Console) -> None:
    table = Table(title="Parity Quantitative Evaluation Scorecard (30 Gates)", border_style="cyan")
    table.add_column("Gate ID", style="bold white")
    table.add_column("Metric Name", style="white")
    table.add_column("Direction", justify="center")
    table.add_column("Threshold", justify="right")
    table.add_column("Observed", justify="right", style="bold")
    table.add_column("Status", justify="center")

    for r in results:
        status_style = "bold green" if r["status"] == "PASS" else ("bold red" if r["status"] == "FAIL" else "bold yellow")
        dir_sym = ">=" if r["target_direction"] == "ge" else "<="
        table.add_row(
            r["gate_id"],
            r["name"],
            dir_sym,
            f"{r['threshold']} {r['unit']}",
            f"{r['observed_value']} {r['unit']}",
            f"[{status_style}]{r['status']}[/{status_style}]"
        )
    console.print(table)

def main() -> int:
    console = Console()
    if not verify_thresholds_lock():
        console.print("[bold red]GATES_MODIFIED_AFTER_LOCK[/bold red]")
        sys.stderr.write("GATES_MODIFIED_AFTER_LOCK\n")
        return 3

    yaml_path = Path("evals/thresholds_parity.yaml")
    thresholds = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}

    report_data = {
        "verified_hash_status": "LOCKED_VALID",
        "total_gates": len(thresholds),
        "gates": []
    }

    dummy_results = []
    for gid in sorted(thresholds.keys()):
        spec = thresholds[gid]
        dummy_results.append(build_gate_row(
            gate_id=gid,
            spec=spec,
            observed_val=0.0,
            status="SKIPPED"
        ))

    report_data["gates"] = dummy_results
    write_json_atomic("evals/parity_report.json", report_data)

    print_evaluation_summary(dummy_results, console)
    return 0

if __name__ == "__main__":
    sys.exit(main())
