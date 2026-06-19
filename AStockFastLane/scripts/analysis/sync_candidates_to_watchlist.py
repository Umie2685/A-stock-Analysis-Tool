from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_PATH = PROJECT_ROOT / "data" / "analysis" / "candidate_watchlist_latest.json"
WATCHLIST_PATH = PROJECT_ROOT / "config" / "watchlist.json"
SYNC_DIR = PROJECT_ROOT / "data" / "analysis"
DEFAULT_LIMIT = 20


def now_local() -> datetime:
    return datetime.now().astimezone()


def rel(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"file not found: {rel(path)}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"JSON decode failed for {rel(path)}: {exc}") from exc
    except OSError as exc:
        raise RuntimeError(f"read failed for {rel(path)}: {exc}") from exc


def infer_market(code: str) -> str:
    if code.startswith(("600", "601", "603", "605", "688")):
        return "SH"
    if code.startswith(("000", "001", "002", "003", "300", "301")):
        return "SZ"
    if code.startswith(("8", "4", "9")):
        return "BJ"
    return "UNKNOWN"


def normalize_code(value: Any) -> str | None:
    if isinstance(value, str):
        code = value.strip()
    elif isinstance(value, int):
        code = f"{value:06d}"
    else:
        return None
    if len(code) == 6 and code.isdigit():
        return code
    return None


def normalize_market(value: Any, code: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip().upper()
    return infer_market(code)


def load_candidates(path: Path) -> tuple[list[dict[str, Any]], int]:
    payload = read_json(path)
    if isinstance(payload, dict):
        raw_items = payload.get("candidates")
        if raw_items is None:
            raw_items = payload.get("items")
    elif isinstance(payload, list):
        raw_items = payload
    else:
        raise RuntimeError("candidate watchlist root must be an object or list")

    if not isinstance(raw_items, list):
        raise RuntimeError("candidate watchlist must contain a candidates/items list")

    candidates = [item for item in raw_items if isinstance(item, dict)]
    return candidates, len(raw_items)


def candidate_to_watchlist_item(candidate: dict[str, Any], created_at: str) -> tuple[dict[str, Any] | None, str]:
    code = normalize_code(candidate.get("code"))
    if code is None:
        return None, "invalid code"

    market = normalize_market(candidate.get("market"), code)
    if market == "UNKNOWN":
        return None, "unsupported market"

    name = candidate.get("name")
    if not isinstance(name, str) or not name.strip():
        return None, "missing name"

    related_concepts = candidate.get("related_concepts", [])
    if not isinstance(related_concepts, list):
        related_concepts = []

    return {
        "code": code,
        "name": name.strip(),
        "market": market,
        "enabled": True,
        "note": "auto_added_from_candidate_watchlist",
        "source": "candidate_watchlist",
        "tags": ["hot_candidate", "auto_added"],
        "heat_score": candidate.get("heat_score"),
        "related_concepts": related_concepts,
        "updated_at": created_at,
    }, ""


def merge_existing_item(item: dict[str, Any], candidate: dict[str, Any], created_at: str) -> bool:
    changed = False

    note = item.get("note", "")
    if note is None:
        note = ""
    if not isinstance(note, str):
        note = str(note)
    marker = "recent_candidate"
    if marker not in note:
        item["note"] = f"{note}; {marker}" if note else marker
        changed = True

    existing_tags = item.get("tags")
    if not isinstance(existing_tags, list):
        existing_tags = []
    merged_tags = list(existing_tags)
    for tag in ["hot_candidate", "recent_candidate"]:
        if tag not in merged_tags:
            merged_tags.append(tag)
    if merged_tags != existing_tags:
        item["tags"] = merged_tags
        changed = True

    for key in ["heat_score", "related_concepts"]:
        value = candidate.get(key)
        if value is not None and item.get(key) != value:
            item[key] = value
            changed = True

    if item.get("source") != "candidate_watchlist":
        item["source"] = "candidate_watchlist"
        changed = True

    if item.get("updated_at") != created_at:
        item["updated_at"] = created_at
        changed = True

    return changed


def make_backup(path: Path, timestamp: str) -> Path:
    backup_path = path.with_name(f"{path.name}.bak.{timestamp}")
    if backup_path.exists():
        raise RuntimeError(f"backup already exists: {rel(backup_path)}")
    try:
        shutil.copy2(path, backup_path)
    except OSError as exc:
        raise RuntimeError(f"backup failed for {rel(path)}: {exc}") from exc
    return backup_path


def write_json(path: Path, payload: Any) -> None:
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"write failed for {rel(path)}: {exc}") from exc


def run_watchlist_check() -> int:
    command = [sys.executable, "scripts/check_watchlist.py"]
    completed = subprocess.run(command, cwd=PROJECT_ROOT, text=True)
    return completed.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync candidate watchlist stocks into config/watchlist.json."
    )
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Candidate limit, default 20.")
    parser.add_argument(
        "--min-heat-score",
        type=float,
        default=None,
        help="Optional minimum heat_score threshold.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit <= 0:
        print("ERROR: --limit must be positive")
        return 2

    created = now_local()
    created_at = created.isoformat(timespec="seconds")
    date_stamp = created.strftime("%Y%m%d")
    backup_stamp = created.strftime("%Y%m%d%H%M%S")

    try:
        candidates, raw_candidate_count = load_candidates(CANDIDATE_PATH)
        watchlist = read_json(WATCHLIST_PATH)
        if not isinstance(watchlist, dict):
            raise RuntimeError("watchlist root must be an object")
        items = watchlist.get("items")
        if not isinstance(items, list):
            raise RuntimeError("watchlist.items must be a list")

        existing_watchlist_count = len(items)
        existing_index: dict[tuple[str, str], dict[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            code = normalize_code(item.get("code"))
            if code is None:
                continue
            market = normalize_market(item.get("market"), code)
            existing_index[(code, market)] = item

        added: list[dict[str, Any]] = []
        skipped_existing: list[dict[str, Any]] = []
        skipped_invalid: list[dict[str, Any]] = []

        selected: list[dict[str, Any]] = []
        for candidate in candidates:
            heat_score = candidate.get("heat_score")
            if args.min_heat_score is not None:
                try:
                    if float(heat_score) < args.min_heat_score:
                        continue
                except (TypeError, ValueError):
                    skipped_invalid.append({"candidate": candidate, "reason": "invalid heat_score"})
                    continue
            selected.append(candidate)
            if len(selected) >= args.limit:
                break

        changed = False
        for candidate in selected:
            new_item, invalid_reason = candidate_to_watchlist_item(candidate, created_at)
            if new_item is None:
                skipped_invalid.append({"candidate": candidate, "reason": invalid_reason})
                continue

            key = (new_item["code"], new_item["market"])
            existing = existing_index.get(key)
            if existing is not None:
                if merge_existing_item(existing, candidate, created_at):
                    changed = True
                skipped_existing.append(
                    {"code": new_item["code"], "name": new_item["name"], "market": new_item["market"]}
                )
                continue

            items.append(new_item)
            existing_index[key] = new_item
            added.append(new_item)
            changed = True

        backup_path: Path | None = None
        if changed:
            backup_path = make_backup(WATCHLIST_PATH, backup_stamp)
            write_json(WATCHLIST_PATH, watchlist)

        sync_payload = {
            "meta": {
                "label": "watchlist_sync",
                "created_at": created_at,
                "source_file": rel(CANDIDATE_PATH),
                "output_file": rel(WATCHLIST_PATH),
                "limit": args.limit,
                "min_heat_score": args.min_heat_score,
                "candidate_count": raw_candidate_count,
                "selected_count": len(selected),
                "existing_watchlist_count": existing_watchlist_count,
                "final_watchlist_count": len(items),
                "added_count": len(added),
                "skipped_existing_count": len(skipped_existing),
                "skipped_invalid_count": len(skipped_invalid),
                "backup_file": rel(backup_path) if backup_path else "",
            },
            "added": added,
            "skipped_existing": skipped_existing,
            "skipped_invalid": skipped_invalid,
            "backup_file": rel(backup_path) if backup_path else "",
            "created_at": created_at,
        }
        SYNC_DIR.mkdir(parents=True, exist_ok=True)
        latest_sync = SYNC_DIR / "watchlist_sync_latest.json"
        dated_sync = SYNC_DIR / f"watchlist_sync_{date_stamp}.json"
        write_json(latest_sync, sync_payload)
        write_json(dated_sync, sync_payload)

        check_rc = run_watchlist_check()
        if check_rc != 0:
            print(f"ERROR: watchlist validation failed with return code {check_rc}")
            return check_rc

        print(f"candidate_count: {raw_candidate_count}")
        print(f"limit: {args.limit}")
        print(f"existing_watchlist_count: {existing_watchlist_count}")
        print(f"added_count: {len(added)}")
        print(f"skipped_existing_count: {len(skipped_existing)}")
        print(f"skipped_invalid_count: {len(skipped_invalid)}")
        print(f"output_file: {rel(WATCHLIST_PATH)}")
        print(f"backup_file: {rel(backup_path) if backup_path else ''}")
        print(f"sync_latest: {rel(latest_sync)}")
        print(f"sync_dated: {rel(dated_sync)}")
        return 0
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
