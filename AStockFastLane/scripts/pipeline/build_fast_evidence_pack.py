from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NEWS_INPUT_PATH = PROJECT_ROOT / "data" / "cache" / "eastmoney_news_probe_latest.json"
ANNOUNCEMENT_INPUT_PATH = (
    PROJECT_ROOT / "data" / "cache" / "cninfo_announcement_probe_latest.json"
)
LATEST_OUTPUT_PATH = PROJECT_ROOT / "data" / "evidence" / "fast_evidence_pack_latest.json"
PACK_NAME = "fast_evidence_pack"
LOCAL_TZ = timezone(timedelta(hours=8))
DISCLAIMER = "本文件仅用于数据整理和研究辅助，不构成投资建议。"
NEWS_CONFIDENCE_NOTE = (
    "Source item normalized from Eastmoney news probe; "
    "no investment conclusion generated."
)
ANNOUNCEMENT_CONFIDENCE_NOTE = (
    "Source item normalized from CNInfo announcement probe; metadata only, PDF not downloaded."
)


def now_local() -> datetime:
    return datetime.now(LOCAL_TZ)


def read_json(path: Path) -> tuple[Any | None, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except FileNotFoundError:
        return None, [f"Input file not found: {path.relative_to(PROJECT_ROOT).as_posix()}"]
    except json.JSONDecodeError as exc:
        return None, [f"JSON decode failed: {path.relative_to(PROJECT_ROOT).as_posix()}: {exc}"]
    except OSError as exc:
        return None, [f"Input read failed: {path.relative_to(PROJECT_ROOT).as_posix()}: {exc}"]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def stable_evidence_id(source: str, category: str, index: int, item: dict[str, Any]) -> str:
    seed = "|".join(
        [
            source,
            category,
            str(item.get("title", "")),
            str(item.get("publish_time", "")),
            str(item.get("url", "")),
        ]
    )
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
    return f"{source}_{category}_{index:03d}_{digest}"


def normalize_news_item(source: str, index: int, item: dict[str, Any]) -> dict[str, Any]:
    title = str(item.get("title") or "").strip()
    publish_time = str(item.get("publish_time") or "").strip()
    item_source = str(item.get("source") or source or "eastmoney_news").strip()
    url = str(item.get("url") or "").strip()
    summary = str(item.get("summary") or "").strip()

    return {
        "evidence_id": stable_evidence_id(source, "news", index, item),
        "source": source or item_source or "eastmoney_news",
        "category": "news",
        "title": title,
        "publish_time": publish_time,
        "url": url,
        "summary": summary,
        "tags": [],
        "related_symbols": [],
        "confidence_note": NEWS_CONFIDENCE_NOTE,
        "raw_ref": {
            "title": title,
            "publish_time": publish_time,
            "source": item_source,
            "url": url,
            "raw": item.get("raw", {}),
        },
    }


def normalize_announcement_item(source: str, index: int, item: dict[str, Any]) -> dict[str, Any]:
    title = str(item.get("title") or "").strip()
    publish_time = str(item.get("publish_time") or "").strip()
    url = str(item.get("url") or "").strip()
    company = str(item.get("company") or "").strip()
    symbol = str(item.get("symbol") or "").strip()
    announcement_type = str(item.get("announcement_type") or "").strip()
    summary_parts = [part for part in [company, symbol, announcement_type] if part]
    summary = " / ".join(summary_parts)

    return {
        "evidence_id": stable_evidence_id(source, "announcement", index, item),
        "source": source or "cninfo_announcement",
        "category": "announcement",
        "title": title,
        "publish_time": publish_time,
        "url": url,
        "summary": summary,
        "tags": [],
        "related_symbols": [symbol] if symbol else [],
        "confidence_note": ANNOUNCEMENT_CONFIDENCE_NOTE,
        "raw_ref": {
            "title": title,
            "publish_time": publish_time,
            "company": company,
            "symbol": symbol,
            "announcement_type": announcement_type,
            "url": url,
            "raw": item.get("raw", {}),
        },
    }


def collect_items(
    path: Path,
    default_source: str,
    category: str,
    errors: list[str],
) -> list[dict[str, Any]]:
    input_data, read_errors = read_json(path)
    errors.extend(read_errors)
    evidence_items: list[dict[str, Any]] = []

    if input_data is None:
        return evidence_items
    if not isinstance(input_data, dict):
        errors.append(f"Input JSON root is not an object: {path.relative_to(PROJECT_ROOT).as_posix()}")
        return evidence_items

    source = str(input_data.get("source") or default_source)
    input_errors = input_data.get("errors")
    if isinstance(input_errors, list):
        errors.extend(f"{source}: {error}" for error in input_errors)

    if input_data.get("success") is not True:
        errors.append(f"{source}: input probe success is not true")

    raw_items = input_data.get("items", [])
    if not isinstance(raw_items, list):
        errors.append(f"{source}: input probe items is not a list")
        return evidence_items

    normalizer = normalize_news_item if category == "news" else normalize_announcement_item
    for index, item in enumerate(raw_items, start=1):
        if isinstance(item, dict):
            evidence_items.append(normalizer(source, index, item))
        else:
            errors.append(f"{source}: skipped non-object item at index {index}")

    if input_data.get("success") is True and not evidence_items:
        errors.append(f"{source}: input probe succeeded but no items were available")

    return evidence_items


def build_pack() -> dict[str, Any]:
    generated_at = now_local().isoformat()
    errors: list[str] = []
    news_items = collect_items(NEWS_INPUT_PATH, "eastmoney_news", "news", errors)
    announcement_items = collect_items(
        ANNOUNCEMENT_INPUT_PATH,
        "cninfo_announcement",
        "announcement",
        errors,
    )
    evidence_items = [*news_items, *announcement_items]

    success = bool(evidence_items) and not errors

    return {
        "pack_name": PACK_NAME,
        "generated_at": generated_at,
        "success": success,
        "sources": ["eastmoney_news", "cninfo_announcement"],
        "item_count": len(evidence_items),
        "news_item_count": len(news_items),
        "announcement_item_count": len(announcement_items),
        "evidence_items": evidence_items,
        "errors": errors,
        "disclaimer": DISCLAIMER,
    }


def upsert_endpoint_results(pack: dict[str, Any], dated_output_path: Path) -> None:
    doc_path = PROJECT_ROOT / "docs" / "endpoint_probe_results.md"
    existing = doc_path.read_text(encoding="utf-8") if doc_path.exists() else "# Endpoint Probe Results\n"
    marker = "## MVP0-008G Multi-source Fast Evidence Pack"
    before = existing.split(marker, 1)[0].rstrip()

    status = "Success" if pack["success"] else "Failed"
    lines = [
        marker,
        "",
        f"Status: {status}",
        "",
        "Inputs:",
        "",
        f"- {NEWS_INPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}",
        f"- {ANNOUNCEMENT_INPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}",
        "",
        "Output files:",
        "",
        f"- {dated_output_path.relative_to(PROJECT_ROOT).as_posix()}",
        f"- {LATEST_OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}",
        "",
        f"News item count: {pack['news_item_count']}",
        f"Announcement item count: {pack['announcement_item_count']}",
        f"Total evidence item count: {pack['item_count']}",
        "",
        "Notes:",
        "",
        "- Built from cached Eastmoney news and CNInfo announcement probe JSON only.",
        "- No network request was made.",
        "- No Markdown report was generated.",
        "- CNInfo announcement records are metadata only; PDFs were not downloaded.",
    ]

    if pack["errors"]:
        lines.extend(["", "Errors:", ""])
        lines.extend(f"- {error}" for error in pack["errors"])

    doc_path.write_text(f"{before}\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def upsert_current_progress(pack: dict[str, Any]) -> None:
    doc_path = PROJECT_ROOT / "docs" / "current_progress.md"
    existing = doc_path.read_text(encoding="utf-8") if doc_path.exists() else "# Current Progress\n"
    marker = "## MVP0-008G"
    before = existing.split(marker, 1)[0].rstrip()
    status = "Completed" if pack["success"] else "Failed"

    lines = [
        marker,
        "",
        f"Status: {status}",
        "",
        "Summary:",
        "",
        "- Merged Eastmoney news and CNInfo announcements into Fast Evidence Pack.",
        "- Generated latest and dated evidence JSON.",
        "- No network request was made.",
        "",
        "Next:",
        "",
        "- MVP0-009G: Upgrade Markdown report to support news + announcements.",
    ]

    if pack["errors"]:
        lines.extend(["", "Errors:", ""])
        lines.extend(f"- {error}" for error in pack["errors"])

    doc_path.write_text(f"{before}\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    pack = build_pack()
    today = now_local().strftime("%Y%m%d")
    dated_output_path = (
        PROJECT_ROOT / "data" / "evidence" / f"fast_evidence_pack_{today}.json"
    )

    write_json(LATEST_OUTPUT_PATH, pack)
    write_json(dated_output_path, pack)
    upsert_endpoint_results(pack, dated_output_path)
    upsert_current_progress(pack)

    print(f"Pack: {PACK_NAME}")
    print(f"News input: {NEWS_INPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Announcement input: {ANNOUNCEMENT_INPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Success: {pack['success']}")
    print(f"News item count: {pack['news_item_count']}")
    print(f"Announcement item count: {pack['announcement_item_count']}")
    print(f"Total evidence item count: {pack['item_count']}")
    print(f"Latest output: {LATEST_OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Dated output: {dated_output_path.relative_to(PROJECT_ROOT).as_posix()}")
    if pack["errors"]:
        print("Errors:")
        for error in pack["errors"]:
            print(f"- {error}")

    return 0 if pack["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

