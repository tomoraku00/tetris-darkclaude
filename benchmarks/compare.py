"""2 つのベンチマーク結果を比較

使い方:
    python benchmarks/compare.py reports/v0.9-beta.json reports/exp-claude-md.json
"""
import csv
import json
import sys
from pathlib import Path


def compare(baseline_path: str, experiment_path: str) -> None:
    try:
        baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Error: file not found - {baseline_path}")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {baseline_path} - {exc}")
        sys.exit(1)

    try:
        experiment = json.loads(Path(experiment_path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Error: file not found - {experiment_path}")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {experiment_path} - {exc}")
        sys.exit(1)

    bv = baseline.get("version", "baseline")
    ev = experiment.get("version", "experiment")

    b_tasks = baseline.get("tasks", {})
    e_tasks = experiment.get("tasks", {})
    bt = baseline.get("totals", {})
    et = experiment.get("totals", {})

    print(f"\n{bv}  →  {ev}\n")
    header = f"{'Task':<24} {'Quality':^17} {'Speed':^17} {'Diff':>10}"
    print(header)
    print("─" * len(header))

    all_tasks = sorted(set(b_tasks) | set(e_tasks))
    for task_id in all_tasks:
        b = b_tasks.get(task_id, {})
        e = e_tasks.get(task_id, {})
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
    print(f"{'Completed':<24} {bt.get('completed', 0):>6} / {et.get('completed', 0):>6}")
    print(f"{'Avg quality':<24} {bt.get('avg_score', 0.0):>6.2f} -> {et.get('avg_score', 0.0):>6.2f}")
    b_sp = bt.get("avg_speed_score", 0.0)
    e_sp = et.get("avg_speed_score", 0.0)
    print(f"{'Avg speed':<24} {b_sp:>6.2f} -> {e_sp:>6.2f}")
    print(f"{'Total duration(s)':<24} {bt.get('total_duration_sec', 0):>6.0f} -> {et.get('total_duration_sec', 0):>6.0f}")


def export_csv(baseline_path: str, experiment_path: str, output_path: str) -> None:
    """2 つのベンチマーク結果を CSV 形式で出力する。

    各タスクごとの品質スコア、速度スコア、差異、および要約統計を CSV に書き出す。

    Args:
        baseline_path: ベースラインの JSON ファイルパス
        experiment_path: 検証対象の JSON ファイルパス
        output_path: 出力先の CSV ファイルパス
    """
    try:
        baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Error: file not found - {baseline_path}")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {baseline_path} - {exc}")
        sys.exit(1)

    try:
        experiment = json.loads(Path(experiment_path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Error: file not found - {experiment_path}")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {experiment_path} - {exc}")
        sys.exit(1)

    b_tasks = baseline.get("tasks", {})
    e_tasks = experiment.get("tasks", {})
    bt = baseline.get("totals", {})
    et = experiment.get("totals", {})

    rows = []

    # ヘッダ
    header = [
        "Task",
        "Baseline_Quality",
        "Experiment_Quality",
        "Quality_Diff",
        "Baseline_Speed",
        "Experiment_Speed",
        "Speed_Diff",
    ]
    rows.append(header)

    all_tasks = sorted(set(b_tasks) | set(e_tasks))
    for task_id in all_tasks:
        b = b_tasks.get(task_id, {})
        e = e_tasks.get(task_id, {})
        b_q = b.get("score", 0.0)
        e_q = e.get("score", 0.0)
        b_s = b.get("speed_score", 0.0)
        e_s = e.get("speed_score", 0.0)
        q_diff = round(e_q - b_q, 4)
        s_diff = round(e_s - b_s, 4)
        rows.append([
            task_id,
            b_q,
            e_q,
            q_diff,
            b_s,
            e_s,
            s_diff,
        ])

    # 要約統計を末尾に追加（空行区切り）
    rows.append([])
    summary_header = [
        "Summary",
        "Baseline_Completed",
        "Experiment_Completed",
        "Baseline_Avg_Quality",
        "Experiment_Avg_Quality",
        "Baseline_Avg_Speed",
        "Experiment_Avg_Speed",
        "Baseline_Total_Duration_s",
        "Experiment_Total_Duration_s",
    ]
    rows.append(summary_header)
    rows.append([
        "",
        bt.get("completed", 0),
        et.get("completed", 0),
        bt.get("avg_score", 0.0),
        et.get("avg_score", 0.0),
        bt.get("avg_speed_score", 0.0),
        et.get("avg_speed_score", 0.0),
        bt.get("total_duration_sec", 0),
        et.get("total_duration_sec", 0),
    ])

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python benchmarks/compare.py <baseline.json> <experiment.json>")
        sys.exit(1)
    compare(sys.argv[1], sys.argv[2])
