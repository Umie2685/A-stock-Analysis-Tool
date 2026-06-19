from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = PROJECT_ROOT / "data" / "evidence" / "fast_evidence_pack_latest.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "fast_report_latest.md"
PROGRESS_PATH = PROJECT_ROOT / "docs" / "current_progress.md"
LOCAL_TZ = timezone(timedelta(hours=8))

STEPS = [
    ("Check watchlist", PROJECT_ROOT / "scripts" / "check_watchlist.py"),
    ("Eastmoney news probe", PROJECT_ROOT / "scripts" / "probes" / "test_eastmoney_news_probe.py"),
    ("CNInfo watchlist announcement probe", PROJECT_ROOT / "scripts" / "probes" / "test_cninfo_announcement_probe.py"),
    ("Eastmoney watchlist research report probe", PROJECT_ROOT / "scripts" / "probes" / "test_eastmoney_report_probe.py"),
    ("Build Fast Evidence Pack", PROJECT_ROOT / "scripts" / "pipeline" / "build_fast_evidence_pack.py"),
    ("Generate grouped Fast Report", PROJECT_ROOT / "scripts" / "pipeline" / "generate_fast_report.py"),
]


def rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def today_string() -> str:
    return datetime.now(LOCAL_TZ).strftime("%Y%m%d")


def run_python_script(name: str, script_path: Path) -> int:
    command = [sys.executable, str(script_path)]
    print(f"START {name}: {sys.executable} {rel(script_path)}", flush=True)
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    print(f"END {name}: returncode={completed.returncode}", flush=True)
    return completed.returncode


def read_evidence_counts() -> tuple[int, int, int, int]:
    payload: dict[str, Any] = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    return (
        int(payload.get("news_item_count") or 0),
        int(payload.get("announcement_item_count") or 0),
        int(payload.get("report_item_count") or payload.get("research_report_item_count") or 0),
        int(payload.get("item_count") or 0),
    )


def upsert_markdown_section(existing: str, marker: str, section_lines: list[str]) -> str:
    section_text = "\n".join(section_lines).rstrip()
    marker_index = existing.find(marker)
    if marker_index < 0:
        return f"{existing.rstrip()}\n\n{section_text}\n"

    next_marker_index = existing.find("\n## ", marker_index + len(marker))
    before = existing[:marker_index].rstrip()
    after = existing[next_marker_index:].lstrip("\n") if next_marker_index >= 0 else ""
    if after:
        return f"{before}\n\n{section_text}\n\n{after.rstrip()}\n"
    return f"{before}\n\n{section_text}\n"


def update_progress_notes() -> None:
    existing = PROGRESS_PATH.read_text(encoding="utf-8") if PROGRESS_PATH.exists() else "# Current Progress\n"
    sections = [
        [
            "## MVP2-006G",
            "",
            "Status: Completed",
            "",
            "Summary:",
            "",
            "- Added scripts/run_mvp2_pipeline.py as the recommended MVP2 refresh entry.",
            "- The pipeline checks config/watchlist.json before running probe steps.",
            "- It refreshes news, watchlist CNInfo announcements, watchlist Eastmoney research reports, Fast Evidence Pack, and grouped Markdown report in order.",
            "- The pipeline stops on the first failed step and returns the failing exit code.",
            "- It prints latest evidence/report paths and news / announcement / research_report / total counts after success.",
            "- It does not add PDF download, LLM calls, third-party dependencies, or investment advice generation.",
            "",
            "Next:",
            "",
            "- MVP2-007G: keep README and progress docs aligned with the three run entries.",
        ],
        [
            "## MVP2-007G",
            "",
            "Status: Completed",
            "",
            "Summary:",
            "",
            "- Documented run_offline_report.py, run_mvp1_pipeline.py, and run_mvp2_pipeline.py.",
            "- Documented config/watchlist.json and the code / name / market / enabled / orgId / note fields.",
            "- Added docs/mvp2_watchlist_report_notes.md for the watchlist grouped report and MVP2 pipeline boundary.",
            "",
            "Next:",
            "",
            "- MVP2 can now proceed to larger watchlist batches while keeping source metadata and no-advice boundaries explicit.",
        ],
    ]

    updated = existing
    for section in sections:
        updated = upsert_markdown_section(updated, section[0], section)
    PROGRESS_PATH.write_text(updated, encoding="utf-8")


def main() -> int:
    print("MVP2 pipeline started.", flush=True)
    print("Boundary: check watchlist, refresh probes, build Fast Evidence Pack, then generate grouped Markdown report.", flush=True)
    print("Boundary: no PDF download, no LLM call, no investment advice generation.", flush=True)

    for name, script_path in STEPS:
        if not script_path.is_file():
            print(f"ERROR: missing script for step '{name}': {rel(script_path)}", flush=True)
            return 1
        return_code = run_python_script(name, script_path)
        if return_code != 0:
            print(f"MVP2 pipeline stopped after failed step: {name}", flush=True)
            return return_code

    try:
        news_count, announcement_count, report_count, item_count = read_evidence_counts()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: failed to read evidence counts from {rel(EVIDENCE_PATH)}: {exc}", flush=True)
        return 1

    update_progress_notes()

    today = today_string()
    dated_evidence_path = PROJECT_ROOT / "data" / "evidence" / f"fast_evidence_pack_{today}.json"
    dated_report_path = PROJECT_ROOT / "reports" / f"fast_report_{today}.md"

    print("MVP2 pipeline completed successfully.", flush=True)
    print(f"Latest evidence: {rel(EVIDENCE_PATH)}", flush=True)
    print(f"Dated evidence: {rel(dated_evidence_path)}", flush=True)
    print(f"Latest report: {rel(REPORT_PATH)}", flush=True)
    print(f"Dated report: {rel(dated_report_path)}", flush=True)
    print(f"News item count: {news_count}", flush=True)
    print(f"Announcement item count: {announcement_count}", flush=True)
    print(f"Research report item count: {report_count}", flush=True)
    print(f"Total evidence item count: {item_count}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
