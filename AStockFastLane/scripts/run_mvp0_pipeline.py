from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    ("Eastmoney news probe", ["scripts/probes/test_eastmoney_news_probe.py"]),
    ("CNInfo announcement probe", ["scripts/probes/test_cninfo_announcement_probe.py"]),
    ("Build Fast Evidence Pack", ["scripts/pipeline/build_fast_evidence_pack.py"]),
    ("Generate Fast Report", ["scripts/pipeline/generate_fast_report.py"]),
]
REPORT_PATH = PROJECT_ROOT / "reports" / "fast_report_latest.md"


def run_step(name: str, script_parts: list[str]) -> int:
    command = [sys.executable, *script_parts]
    print(f"START {name}: {' '.join(command)}")
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    print(f"END {name}: returncode={completed.returncode}")
    return completed.returncode


def main() -> int:
    for name, command in STEPS:
        return_code = run_step(name, command)
        if return_code != 0:
            print(f"Pipeline stopped after failed step: {name}")
            return return_code

    print("MVP0 pipeline completed successfully.")
    print(f"Final report: {REPORT_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

