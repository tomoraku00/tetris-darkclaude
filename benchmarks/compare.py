"""2 つのベンチマーク結果を比較

使い方:
    python benchmarks/compare.py reports/v0.9-beta.json reports/exp-claude-md.json
"""
import json
import sys
from pathlib import Path


def compare(baseline_path: str, experiment_path: str) -> None:
    baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    experiment = json.loads(Path(experiment_path).read_text(encoding="utf-8"))

    bv = baseline.get("version", "baseline")
    ev = experiment.get("version", "experiment")

    print(f"\n{bv}  →  {ev}\n")
    print(f"{'Task':<28} {'Base':>6} {'Exp':>6} {'Diff':>7}  {'Time(s)':>8}")
    print("─" * 60)

    all_tasks = sorted(set(baseline["tasks"]) | set(experiment["tasks"]))
    for task_id in all_tasks:
        b = baseline["tasks"].get(task_id, {})
        e = experiment["tasks"].get(task_id, {})
        b_score = b.get("score", 0.0)
        e_score = e.get("score", 0.0)
        diff = e_score - b_score
        arrow = "↑" if diff > 0.01 else ("↓" if diff < -0.01 else "·")
        e_dur = e.get("duration_sec", 0.0)
        b_dur = b.get("duration_sec", 0.0)
        dur_info = f"{b_dur:.0f}→{e_dur:.0f}"
        print(
            f"{task_id:<28} {b_score:>6.2f} {e_score:>6.2f} {arrow}{abs(diff):>6.2f}  {dur_info:>8}"
        )

    print("─" * 60)
    bt = baseline["totals"]
    et = experiment["totals"]
    print(f"{'Completed':<28} {bt['completed']:>6} {et['completed']:>6}")
    print(f"{'Avg score':<28} {bt['avg_score']:>6.2f} {et['avg_score']:>6.2f}")
    print(f"{'Total duration(s)':<28} {bt['total_duration_sec']:>6.0f} {et['total_duration_sec']:>6.0f}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python benchmarks/compare.py <baseline.json> <experiment.json>")
        sys.exit(1)
    compare(sys.argv[1], sys.argv[2])
