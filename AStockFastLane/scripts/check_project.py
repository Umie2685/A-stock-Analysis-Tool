from __future__ import annotations

from pathlib import Path

from utils.io_utils import read_json, write_json
from utils.logging_utils import get_logger


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRS = [
    "configs",
    "scripts/probes",
    "scripts/providers",
    "scripts/pipeline",
    "scripts/utils",
    "data/raw",
    "data/cache",
    "data/evidence",
    "data/manual",
    "reports",
    "docs",
]

REQUIRED_FILES = [
    "README.md",
    "requirements.txt",
    "configs/data_sources.yaml",
    "configs/watchlist_template.txt",
    "scripts/probes/__init__.py",
    "scripts/providers/__init__.py",
    "scripts/pipeline/__init__.py",
    "scripts/utils/__init__.py",
    "scripts/utils/io_utils.py",
    "scripts/utils/logging_utils.py",
    "scripts/check_project.py",
    "scripts/run_mvp0_pipeline.py",
    "docs/current_progress.md",
    "docs/data_source_notes.md",
    "docs/endpoint_probe_results.md",
    "docs/mvp0_release_notes.md",
    "docs/context_summary.md",
]


def main() -> int:
    logger = get_logger("check_project")
    failures: list[str] = []

    for directory in REQUIRED_DIRS:
        path = PROJECT_ROOT / directory
        if path.is_dir():
            logger.info("DIR OK: %s", directory)
        else:
            failures.append(f"Missing directory: {directory}")
            logger.error("DIR MISSING: %s", directory)

    for file_name in REQUIRED_FILES:
        path = PROJECT_ROOT / file_name
        if path.is_file():
            logger.info("FILE OK: %s", file_name)
        else:
            failures.append(f"Missing file: {file_name}")
            logger.error("FILE MISSING: %s", file_name)

    check_payload = {
        "project": "AStockFastLane",
        "stage": "MVP0-001",
        "check": "ok",
    }
    check_path = PROJECT_ROOT / "data/cache/check_project.json"
    write_json(check_path, check_payload)
    loaded_payload = read_json(check_path)

    if loaded_payload == check_payload:
        logger.info("JSON IO OK: data/cache/check_project.json")
    else:
        failures.append("JSON roundtrip failed")
        logger.error("JSON IO FAILED: data/cache/check_project.json")

    if failures:
        logger.error("Project check failed.")
        for failure in failures:
            logger.error(failure)
        return 1

    print("AStockFastLane project check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
