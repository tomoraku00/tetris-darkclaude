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
    header = f"{'Task':<24} {'Quality':^17} {'Speed':^17} {'Diff':>10}"
    print(header)
    print("─" * len(header))

    all_tasks = sorted(set(baseline["tasks"]) | set(experiment["tasks"]))
    for task_id in all_tasks:
        b = baseline["tasks"].get(task_id, {})
        e = experiment["tasks"].get(task_id, {})
        b_q = b.get("score", 0.0)
        e_q = e.get("score", 0.0)
        b_s = b.get("speed_score", 0.0)
        e_s = e.get("speed_score", 0.0)
        q_diff = e_q - b_q
        s_diff = e_s - b_s
        q_arrow = "^" if q_diff > 0.01 else ("v" if q_diff < -0.01 else "-")
        s_arrow = "^" if s_diff > 0.01 else ("v" if s_diff < -0.01 else "-")
        quality_col = f"{b_q:.2f} -> {e_q:.2f}"
        speed_col = f"{b_s:.2f} -> {e_s:.2f}"
        diff_col = f"Q{q_arrow}{abs(q_diff):.2f} S{s_arrow}{abs(s_diff):.2f}"
        print(f"{task_id:<24} {quality_col:^17} {speed_col:^17} {diff_col:>10}")

    print("─" * len(header))
    bt = baseline["totals"]
    et = experiment["totals"]
    print(f"{'Completed':<24} {bt['completed']:>6} / {et['completed']:>6}")
    print(f"{'Avg quality':<24} {bt['avg_score']:>6.2f} -> {et['avg_score']:>6.2f}")
    b_sp = bt.get("avg_speed_score", 0.0)
    e_sp = et.get("avg_speed_score", 0.0)
    print(f"{'Avg speed':<24} {b_sp:>6.2f} -> {e_sp:>6.2f}")
    print(f"{'Total duration(s)':<24} {bt['total_duration_sec']:>6.0f} -> {et['total_duration_sec']:>6.0f}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python benchmarks/compare.py <baseline.json> <experiment.json>")
        sys.exit(1)
    compare(sys.argv[1], sys.argv[2])
