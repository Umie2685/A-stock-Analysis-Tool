from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NEWS_INPUT_PATH = PROJECT_ROOT / "data" / "cache" / "eastmoney_news_probe_latest.json"
ANNOUNCEMENT_INPUT_PATH = (
    PROJECT_ROOT / "data" / "cache" / "cninfo_announcement_probe_latest.json"
)
REPORT_INPUT_PATH = PROJECT_ROOT / "data" / "cache" / "eastmoney_report_probe_latest.json"
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
REPORT_CONFIDENCE_NOTE = (
    "Source item normalized from Eastmoney report probe; institution opinion metadata only, "
    "no investment conclusion generated."
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
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


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


def text_value(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def raw_text(raw: dict[str, Any], keys: tuple[str, ...], fallback: str = "") -> str:
    for key in keys:
        value = raw.get(key)
        text = text_value(value)
        if text:
            return text
    return fallback


def normalize_news_item(source: str, index: int, item: dict[str, Any]) -> dict[str, Any]:
    title = str(item.get("title") or "").strip()
    publish_time = str(item.get("publish_time") or "").strip()
    item_source = str(item.get("source") or source or "eastmoney_news").strip()
    url = str(item.get("url") or "").strip()
    summary = str(item.get("summary") or "").strip()

    return {
        "evidence_id": stable_evidence_id(source, "news", index, item),
        "source": source or item_source or "eastmoney_news",
        "evidence_type": "news",
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
    raw = item.get("raw", {})
    if not isinstance(raw, dict):
        raw = {}

    title = text_value(item.get("title") or raw_text(raw, ("announcementTitle", "shortTitle")))
    publish_time = text_value(item.get("publish_time"))
    announcement_date = publish_time
    url = text_value(item.get("url"))
    query_code = text_value(item.get("query_code"))
    query_name = text_value(item.get("query_name"))
    query_market = text_value(item.get("query_market"))
    query_org_id = text_value(item.get("query_orgId") or item.get("query_org_id"))
    stock_code = text_value(item.get("stock_code") or item.get("symbol") or raw_text(raw, ("secCode",)), query_code)
    stock_name = text_value(item.get("stock_name") or item.get("company") or raw_text(raw, ("secName", "tileSecName")), query_name)
    company = text_value(item.get("company"), stock_name)
    symbol = text_value(item.get("symbol"), stock_code)
    announcement_type = text_value(
        item.get("announcement_type") or raw_text(raw, ("announcementTypeName", "announcementType"))
    )
    adjunct_url = text_value(item.get("adjunctUrl") or raw_text(raw, ("adjunctUrl",)))
    summary_parts = [part for part in [company, symbol, announcement_type] if part]
    summary = " / ".join(summary_parts)

    return {
        "evidence_id": stable_evidence_id(source, "announcement", index, item),
        "source": source or "cninfo_announcement",
        "evidence_type": "announcement",
        "category": "announcement",
        "query_code": query_code,
        "query_name": query_name,
        "query_market": query_market,
        "query_orgId": query_org_id,
        "stock_code": stock_code,
        "stock_name": stock_name,
        "title": title,
        "publish_time": publish_time,
        "announcement_date": announcement_date,
        "announcement_type": announcement_type,
        "url": url,
        "adjunctUrl": adjunct_url,
        "summary": summary,
        "tags": [],
        "related_symbols": [stock_code] if stock_code else [],
        "confidence_note": ANNOUNCEMENT_CONFIDENCE_NOTE,
        "raw_ref": {
            "title": title,
            "publish_time": publish_time,
            "announcement_date": announcement_date,
            "query_code": query_code,
            "query_name": query_name,
            "query_market": query_market,
            "query_orgId": query_org_id,
            "company": company,
            "symbol": symbol,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "announcement_type": announcement_type,
            "url": url,
            "adjunctUrl": adjunct_url,
            "raw": raw,
        },
    }


def normalize_report_item(source: str, index: int, item: dict[str, Any]) -> dict[str, Any]:
    raw = item.get("raw", {})
    if not isinstance(raw, dict):
        raw = {}

    title = text_value(item.get("title") or raw_text(raw, ("title", "reportTitle")))
    publish_time = text_value(item.get("publish_time") or raw_text(raw, ("publishDate", "publishTime")))[:10]
    url = text_value(item.get("url"))
    query_code = text_value(item.get("query_code"))
    query_name = text_value(item.get("query_name"))
    query_market = text_value(item.get("query_market"))
    stock_code = text_value(item.get("stock_code") or item.get("symbol") or raw_text(raw, ("stockCode",)), query_code)
    stock_name = text_value(item.get("stock_name") or item.get("company") or raw_text(raw, ("stockName",)), query_name)
    institution = text_value(item.get("institution") or raw_text(raw, ("orgSName", "orgName")))
    analyst = text_value(item.get("analyst") or raw_text(raw, ("researcher", "author")))
    company = text_value(item.get("company"), stock_name)
    symbol = text_value(item.get("symbol"), stock_code)
    rating = text_value(item.get("rating") or raw_text(raw, ("emRatingName", "sRatingName")))
    summary_parts = [
        f"institution={institution}" if institution else "",
        f"analyst={analyst}" if analyst else "",
        f"company={company}" if company else "",
        f"rating={rating}" if rating else "",
    ]
    summary = " / ".join(part for part in summary_parts if part)

    return {
        "evidence_id": stable_evidence_id(source, "research_report", index, item),
        "source": source or "eastmoney_report",
        "evidence_type": "research_report",
        "category": "research_report",
        "query_code": query_code,
        "query_name": query_name,
        "query_market": query_market,
        "stock_code": stock_code,
        "stock_name": stock_name,
        "title": title,
        "publish_time": publish_time,
        "institution": institution,
        "analyst": analyst,
        "rating": rating,
        "url": url,
        "summary": summary,
        "tags": [],
        "related_symbols": [stock_code] if stock_code else [],
        "confidence_note": REPORT_CONFIDENCE_NOTE,
        "raw_ref": {
            "title": title,
            "publish_time": publish_time,
            "query_code": query_code,
            "query_name": query_name,
            "query_market": query_market,
            "institution": institution,
            "analyst": analyst,
            "company": company,
            "symbol": symbol,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "rating": rating,
            "url": url,
            "raw": raw,
        },
    }


def collect_items(
    path: Path,
    default_source: str,
    category: str,
    normalizer: Callable[[str, int, dict[str, Any]], dict[str, Any]],
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
    news_items = collect_items(
        NEWS_INPUT_PATH,
        "eastmoney_news",
        "news",
        normalize_news_item,
        errors,
    )
    announcement_items = collect_items(
        ANNOUNCEMENT_INPUT_PATH,
        "cninfo_announcement",
        "announcement",
        normalize_announcement_item,
        errors,
    )
    report_items = collect_items(
        REPORT_INPUT_PATH,
        "eastmoney_report",
        "research_report",
        normalize_report_item,
        errors,
    )
    evidence_items = [*news_items, *announcement_items, *report_items]

    return {
        "pack_name": PACK_NAME,
        "generated_at": generated_at,
        "success": bool(evidence_items) and not errors,
        "sources": ["eastmoney_news", "cninfo_announcement", "eastmoney_report"],
        "item_count": len(evidence_items),
        "news_item_count": len(news_items),
        "announcement_item_count": len(announcement_items),
        "report_item_count": len(report_items),
        "evidence_items": evidence_items,
        "errors": errors,
        "disclaimer": DISCLAIMER,
    }


def replace_or_append_section(existing: str, marker: str, lines: list[str]) -> str:
    section = "\n".join(lines).rstrip() + "\n"
    if marker not in existing:
        return existing.rstrip() + "\n\n" + section

    before, after_marker = existing.split(marker, 1)
    next_index = after_marker.find("\n## ")
    after = "" if next_index == -1 else after_marker[next_index:]
    return before.rstrip() + "\n\n" + section + after.rstrip() + "\n"


def upsert_endpoint_results(pack: dict[str, Any], dated_output_path: Path) -> None:
    doc_path = PROJECT_ROOT / "docs" / "endpoint_probe_results.md"
    existing = doc_path.read_text(encoding="utf-8") if doc_path.exists() else "# Endpoint Probe Results\n"
    marker = "## MVP1-002G Multi-source Fast Evidence Pack with Reports"

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
        f"- {REPORT_INPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}",
        "",
        "Output files:",
        "",
        f"- {dated_output_path.relative_to(PROJECT_ROOT).as_posix()}",
        f"- {LATEST_OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}",
        "",
        f"News item count: {pack['news_item_count']}",
        f"Announcement item count: {pack['announcement_item_count']}",
        f"Report item count: {pack['report_item_count']}",
        f"Total evidence item count: {pack['item_count']}",
        "",
        "Notes:",
        "",
        "- Built from cached Eastmoney news, CNInfo announcement, and Eastmoney report probe JSON only.",
        "- No network request was made.",
        "- No Markdown report was generated.",
        "- CNInfo announcement records are metadata only; PDFs were not downloaded.",
        "- Eastmoney report records are institution opinion metadata only; no investment conclusion was generated.",
    ]

    if pack["errors"]:
        lines.extend(["", "Errors:", ""])
        lines.extend(f"- {error}" for error in pack["errors"])

    doc_path.write_text(replace_or_append_section(existing, marker, lines), encoding="utf-8")


def upsert_current_progress(pack: dict[str, Any]) -> None:
    doc_path = PROJECT_ROOT / "docs" / "current_progress.md"
    existing = doc_path.read_text(encoding="utf-8") if doc_path.exists() else "# Current Progress\n"
    marker = "## MVP1-002G"
    status = "Completed" if pack["success"] else "Failed"

    lines = [
        marker,
        "",
        f"Status: {status}",
        "",
        "Summary:",
        "",
        "- Merged Eastmoney news, CNInfo announcements, and Eastmoney reports into Fast Evidence Pack.",
        "- Generated latest and dated evidence JSON.",
        "- No network request was made.",
        "",
        "Next:",
        "",
        "- MVP1-003G: Upgrade Markdown report to support news + announcements + research reports.",
    ]

    if pack["errors"]:
        lines.extend(["", "Errors:", ""])
        lines.extend(f"- {error}" for error in pack["errors"])

    doc_path.write_text(replace_or_append_section(existing, marker, lines), encoding="utf-8")


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
    print(f"Report input: {REPORT_INPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Success: {pack['success']}")
    print(f"News item count: {pack['news_item_count']}")
    print(f"Announcement item count: {pack['announcement_item_count']}")
    print(f"Report item count: {pack['report_item_count']}")
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
