from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = PROJECT_ROOT / "data" / "analysis" / "candidate_watchlist_latest.json"
DAILY_K_PATH = PROJECT_ROOT / "data" / "market" / "daily_k_latest.json"
TREND_JSON_PATH = PROJECT_ROOT / "data" / "analysis" / "trend_analysis_latest.json"
TREND_MD_PATH = PROJECT_ROOT / "reports" / "trend_analysis_latest.md"
DAILY_K_PROBE = PROJECT_ROOT / "scripts" / "probes" / "test_daily_k_probe.py"
TREND_ANALYZER = PROJECT_ROOT / "scripts" / "analysis" / "analyze_trends.py"
DEFAULT_LIMIT = 20


def rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def read_json_object(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_step(name: str, command: list[str]) -> int:
    printable = " ".join(command)
    print(f"START {name}: {printable}", flush=True)
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    print(f"END {name}: returncode={completed.returncode}", flush=True)
    if completed.returncode != 0:
        print(f"ERROR: failed command for step '{name}': {printable}", flush=True)
        print(f"ERROR: return code: {completed.returncode}", flush=True)
    return completed.returncode


def require_file(path: Path, label: str) -> bool:
    if path.is_file():
        return True
    print(f"ERROR: missing {label}: {rel(path)}", flush=True)
    return False


def daily_summary() -> dict[str, Any]:
    payload = read_json_object(DAILY_K_PATH)
    meta = payload.get("meta", {})
    items = payload.get("items", [])
    if not isinstance(meta, dict):
        meta = {}
    if not isinstance(items, list):
        items = []
    return {
        "item_count": meta.get("item_count", len(items)),
        "ok_count": meta.get("ok_count", sum(1 for item in items if isinstance(item, dict) and item.get("data_status") == "ok")),
        "failed_count": meta.get("failed_count", sum(1 for item in items if isinstance(item, dict) and item.get("data_status") != "ok")),
        "source": meta.get("source", "-"),
        "limit": meta.get("limit", "-"),
        "days": meta.get("days", "-"),
    }


def trend_summary() -> dict[str, Any]:
    payload = read_json_object(TREND_JSON_PATH)
    meta = payload.get("meta", {})
    items = payload.get("items", [])
    if not isinstance(meta, dict):
        meta = {}
    if not isinstance(items, list):
        items = []
    return {
        "item_count": meta.get("item_count", len(items)),
        "ok_count": meta.get("ok_count", "-"),
        "unknown_count": meta.get("unknown_count", "-"),
        "state_counts": meta.get("state_counts", {}),
        "method": meta.get("method", "-"),
    }


def print_summary() -> None:
    daily = daily_summary()
    trend = trend_summary()
    print("MVP4 pipeline completed.", flush=True)
    print(f"daily_k items: {daily['item_count']}", flush=True)
    print(f"daily_k ok: {daily['ok_count']}", flush=True)
    print(f"daily_k failed: {daily['failed_count']}", flush=True)
    print(f"daily_k source: {daily['source']}", flush=True)
    print(f"trend_analysis items: {trend['item_count']}", flush=True)
    print(f"trend_analysis ok: {trend['ok_count']}", flush=True)
    print(f"trend_analysis unknown: {trend['unknown_count']}", flush=True)
    print(f"state_counts: {trend['state_counts']}", flush=True)
    print("output files:", flush=True)
    print(f"- {rel(DAILY_K_PATH)}", flush=True)
    print(f"- {rel(TREND_JSON_PATH)}", flush=True)
    print(f"- {rel(TREND_MD_PATH)}", flush=True)
    print("Next:", flush=True)
    print("python scripts/run_web_dashboard.py", flush=True)
    print("open http://127.0.0.1:8000/trend-analysis", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the MVP4 daily K and trend-analysis pipeline.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Candidate count limit, default 20.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    limit = max(1, args.limit)
    print("MVP4 pipeline started.", flush=True)
    print("Boundary: low-frequency daily K probe plus rule_based trend analysis.", flush=True)
    print("Boundary: no dashboard auto-start, no order placement, no order-book data, no high-frequency data.", flush=True)

    if not require_file(CANDIDATE_PATH, "candidate watchlist input"):
        return 1

    daily_code = run_step(
        "Daily K probe",
        [sys.executable, rel(DAILY_K_PROBE), "--limit", str(limit)],
    )
    if daily_code != 0:
        return daily_code
    if not require_file(DAILY_K_PATH, "daily K output"):
        return 1

    trend_code = run_step(
        "Rule-based trend analysis",
        [sys.executable, rel(TREND_ANALYZER)],
    )
    if trend_code != 0:
        return trend_code
    if not require_file(TREND_JSON_PATH, "trend JSON output"):
        return 1
    if not require_file(TREND_MD_PATH, "trend Markdown output"):
        return 1

    try:
        print_summary()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: failed to read MVP4 summary outputs: {exc}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
