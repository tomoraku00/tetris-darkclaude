"""ベンチマーク実行スクリプト

使い方:
    # Ollama 使用時
    python benchmarks/runner.py --version v0.9-beta --output benchmarks/reports/v0.9-beta.json --client ollama --model qwen3:8b

    # llama-server 使用時
    python benchmarks/runner.py --version v0.9-beta --output benchmarks/reports/v0.9-beta.json --client openai --base-url http://localhost:8080

    # 特定タスクのみ
    python benchmarks/runner.py --tasks T01,T02 --version v0.9-beta --output benchmarks/reports/quick.json --client ollama
"""
import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent.resolve()
_MAIN_PY = _PROJECT_ROOT / "main.py"
_TASK_TIMEOUT = 300  # 秒 (1 タスク最大 5 分)


class BenchmarkRunner:
    def __init__(
        self,
        version: str,
        tasks_dir: Path,
        fixtures_dir: Path,
        model: str | None = None,
        client: str | None = None,
        base_url: str | None = None,
    ):
        self.version = version
        self.tasks_dir = tasks_dir
        self.fixtures_dir = fixtures_dir
        self.model = model
        self.client = client
        self.base_url = base_url
        self.results: dict = {}

    def run_task(self, task_id: str) -> dict:
        task_dir = self.tasks_dir / task_id
        if not task_dir.exists():
            return {"error": f"task_not_found: {task_id}"}

        print(f"  setup...")
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)

            try:
                self._setup_task(task_dir, workdir)
            except Exception as e:
                return {"error": f"setup_failed: {e}"}

            prompt = (task_dir / "prompt.txt").read_text(encoding="utf-8").strip()

            print(f"  running DarkClaude...")
            start = time.monotonic()
            dc_result = self._run_darkclaude(prompt, workdir)
            duration = time.monotonic() - start

            if "error" in dc_result:
                return {
                    "completed": False,
                    "score": 0.0,
                    "duration_sec": round(duration, 1),
                    "tool_calls": 0,
                    "error": dc_result["error"],
                    "output": "",
                }

            print(f"  evaluating...")
            try:
                score = self._evaluate(task_dir, workdir, dc_result)
            except Exception as e:
                score = 0.0
                print(f"  [warn] evaluate failed: {e}")

            return {
                "completed": score >= 0.5,
                "score": round(score, 3),
                "duration_sec": round(duration, 1),
                "tool_calls": dc_result.get("tool_calls", 0),
                "output": dc_result.get("output", "")[:500],
            }

    def _setup_task(self, task_dir: Path, workdir: Path) -> None:
        spec = importlib.util.spec_from_file_location("setup", task_dir / "setup.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.setup(workdir, self.fixtures_dir)

    def _run_darkclaude(self, prompt: str, workdir: Path) -> dict:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            out_json = Path(f.name)

        cmd = [
            sys.executable, str(_MAIN_PY),
            "--prompt", prompt,
            "--workdir", str(workdir),
            "--output-json", str(out_json),
        ]
        if self.model:
            cmd += ["--model", self.model]
        if self.client:
            cmd += ["--client", self.client]
        if self.base_url:
            cmd += ["--base-url", self.base_url]

        try:
            r = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=_TASK_TIMEOUT,
                cwd=str(_PROJECT_ROOT),
            )
        except subprocess.TimeoutExpired:
            return {"error": f"timeout ({_TASK_TIMEOUT}s)"}
        except Exception as e:
            return {"error": str(e)}

        if r.returncode != 0:
            stderr_snippet = r.stderr[-500:] if r.stderr else ""
            return {"error": f"returncode={r.returncode}", "stderr": stderr_snippet}

        try:
            return json.loads(out_json.read_text(encoding="utf-8"))
        except Exception as e:
            return {"error": f"output_json_parse_failed: {e}"}
        finally:
            try:
                out_json.unlink(missing_ok=True)
            except Exception:
                pass

    def _evaluate(self, task_dir: Path, workdir: Path, result: dict) -> float:
        spec = importlib.util.spec_from_file_location("evaluate", task_dir / "evaluate.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return float(mod.evaluate(workdir, result))

    def run_all(self, task_ids: list[str]) -> dict:
        for task_id in task_ids:
            print(f"\n[{task_id}]")
            self.results[task_id] = self.run_task(task_id)
            r = self.results[task_id]
            status = "OK" if r.get("completed") else "NG"
            score = r.get("score", 0.0)
            duration = r.get("duration_sec", 0.0)
            print(f"  {status} score={score:.2f}  {duration:.0f}s")

        return {
            "version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": self.model or "default",
            "tasks": self.results,
            "totals": self._compute_totals(),
        }

    def _compute_totals(self) -> dict:
        completed = sum(1 for r in self.results.values() if r.get("completed"))
        total_duration = sum(r.get("duration_sec", 0) for r in self.results.values())
        scores = [r.get("score", 0) for r in self.results.values()]
        avg_score = sum(scores) / max(len(scores), 1)
        return {
            "completed": completed,
            "total": len(self.results),
            "failed": len(self.results) - completed,
            "total_duration_sec": round(total_duration, 1),
            "avg_score": round(avg_score, 3),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="DarkClaude ベンチマーク runner")
    parser.add_argument("--version", required=True, help="バージョン識別子 (例: v0.9-beta)")
    parser.add_argument("--tasks", default="all", help="カンマ区切りタスク ID、または 'all'")
    parser.add_argument("--output", required=True, help="レポート出力先 JSON パス")
    parser.add_argument("--model", default=None, help="使用モデルを上書き")
    parser.add_argument("--client", default=None, choices=["ollama", "openai"], help="クライアント種別を上書き")
    parser.add_argument("--base-url", default=None, dest="base_url", help="API ベース URL を上書き (openai 時)")
    args = parser.parse_args()

    tasks_dir = Path(__file__).parent / "tasks"
    fixtures_dir = Path(__file__).parent / "fixtures"

    if args.tasks == "all":
        task_ids = sorted(d.name for d in tasks_dir.iterdir() if d.is_dir())
    else:
        task_ids = [t.strip() for t in args.tasks.split(",")]

    print(f"=== DarkClaude Benchmark [{args.version}] ===")
    print(f"Tasks: {', '.join(task_ids)}")
    if args.model:
        print(f"Model: {args.model}")
    if args.client:
        print(f"Client: {args.client}")

    runner = BenchmarkRunner(
        args.version, tasks_dir, fixtures_dir,
        model=args.model,
        client=args.client,
        base_url=getattr(args, "base_url", None),
    )
    report = runner.run_all(task_ids)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    t = report["totals"]
    print(f"\n=== Summary [{args.version}] ===")
    print(f"Completed : {t['completed']} / {t['total']}")
    print(f"Avg score : {t['avg_score']:.2f}")
    print(f"Duration  : {t['total_duration_sec']:.1f}s")
    print(f"Report    : {output_path}")


if __name__ == "__main__":
    main()
