from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATUS_PATH = PROJECT_ROOT / "data" / "manual" / "candidate_review_status.json"
ALLOWED_STATUS = ["pending", "watch", "skip", "confirmed", "rejected"]
TZ = timezone(timedelta(hours=8))


def now_text() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def today_text() -> str:
    return datetime.now(TZ).date().isoformat()


def parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("--confirmed-by-user must be true or false")


def read_status_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "version": 1,
            "description": "Manual review status for candidate_review items. This file does not auto-sync to watchlist.",
            "updated_at": now_text(),
            "sync_mode": "manual_confirm",
            "allowed_status": ALLOWED_STATUS,
            "items": [],
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("status file root must be an object")
    items = payload.get("items", [])
    if not isinstance(items, list):
        payload["items"] = []
    allowed = payload.get("allowed_status")
    if not isinstance(allowed, list) or not allowed:
        payload["allowed_status"] = ALLOWED_STATUS
    return payload


def write_status_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def upsert_status(payload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    allowed = [str(item) for item in payload.get("allowed_status", ALLOWED_STATUS)]
    if args.status not in allowed:
        raise ValueError(f"status must be one of: {', '.join(allowed)}")

    updated_at = now_text()
    review_date = args.review_date or today_text()
    items = payload.setdefault("items", [])
    if not isinstance(items, list):
        items = []
        payload["items"] = items

    target = None
    for item in items:
        if isinstance(item, dict) and str(item.get("code", "")).strip() == args.code:
            target = item
            break

    if target is None:
        target = {
            "code": args.code,
            "name": args.name or "-",
            "market": args.market or "-",
            "review_date": review_date,
            "source": "candidate_review",
            "review_bucket": args.bucket or "-",
            "tags": [],
        }
        items.append(target)
    else:
        if args.name:
            target["name"] = args.name
        if args.market:
            target["market"] = args.market
        if args.bucket:
            target["review_bucket"] = args.bucket
        target["review_date"] = review_date
        target["source"] = "candidate_review"

    target["status"] = args.status
    target["confirmed_by_user"] = bool(args.confirmed_by_user)
    target["review_note"] = args.note or target.get("review_note", "-")
    target["updated_at"] = updated_at
    payload["updated_at"] = updated_at
    payload["sync_mode"] = "manual_confirm"
    return target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update one local candidate_review manual status item.")
    parser.add_argument("--code", required=True)
    parser.add_argument("--status", required=True, choices=ALLOWED_STATUS)
    parser.add_argument("--note", default="")
    parser.add_argument("--name", default="")
    parser.add_argument("--market", default="")
    parser.add_argument("--review-date", default="")
    parser.add_argument("--bucket", default="")
    parser.add_argument("--confirmed-by-user", type=parse_bool, default=False)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    payload = read_status_file(STATUS_PATH)
    item = upsert_status(payload, args)
    write_status_file(STATUS_PATH, payload)
    print(
        "updated "
        f"code={item.get('code', '-')} "
        f"name={item.get('name', '-')} "
        f"status={item.get('status', '-')} "
        f"confirmed_by_user={item.get('confirmed_by_user', False)}"
    )
    print(f"status file path: {STATUS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
