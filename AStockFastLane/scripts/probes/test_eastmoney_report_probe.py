from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from utils.io_utils import write_json  # noqa: E402
from utils.watchlist_loader import DEFAULT_WATCHLIST_PATH, WatchlistError, load_watchlist  # noqa: E402


SOURCE = "eastmoney_report"
PROBE_NAME = "eastmoney_report_probe"
ENDPOINT_BASE = "https://reportapi.eastmoney.com/report/list"
TIMEOUT_SECONDS = 15
PAGE_SIZE = 10
LOCAL_TZ = timezone(timedelta(hours=8))


def now_local() -> datetime:
    return datetime.now(LOCAL_TZ)


def build_params(stock: dict[str, Any]) -> dict[str, str]:
    return {
        "industryCode": "*",
        "pageSize": str(PAGE_SIZE),
        "industry": "*",
        "rating": "*",
        "ratingChange": "*",
        "beginTime": "2000-01-01",
        "endTime": "2030-01-01",
        "pageNo": "1",
        "fields": "",
        "qType": "0",
        "orgCode": "",
        "code": str(stock.get("code") or ""),
        "rcode": "",
        "p": "1",
        "pageNum": "1",
        "pageNumber": "1",
    }


def build_endpoint(stock: dict[str, Any]) -> str:
    return f"{ENDPOINT_BASE}?{urlencode(build_params(stock))}"


def fetch_json(stock: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    endpoint = build_endpoint(stock)
    request = Request(
        endpoint,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0 Safari/537.36"
            ),
            "Referer": "https://data.eastmoney.com/",
            "Accept": "application/json,text/plain,*/*",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        return None, [f"HTTPError: status={exc.code} reason={exc.reason}"]
    except URLError as exc:
        return None, [f"URLError: {exc.reason}"]
    except TimeoutError as exc:
        return None, [f"TimeoutError: {exc}"]
    except OSError as exc:
        return None, [f"OSError: {exc}"]

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        return None, [f"JSONDecodeError: {exc}"]

    if not isinstance(payload, dict):
        return None, ["Unexpected JSON root: expected object"]

    return payload, []


def extract_raw_items(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    result = payload.get("result")
    candidates = [
        payload.get("data"),
        payload.get("Data"),
        result.get("data") if isinstance(result, dict) else None,
        result.get("Data") if isinstance(result, dict) else None,
    ]

    for candidate in candidates:
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)][:PAGE_SIZE], []

    return [], ["Unexpected response: no supported report list field found"]


def first_text(raw: dict[str, Any], keys: tuple[str, ...], default: str = "") -> str:
    for key in keys:
        value = raw.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return default


def normalize_item(raw: dict[str, Any], stock: dict[str, Any]) -> dict[str, Any]:
    query_code = str(stock.get("code") or "").strip()
    query_name = str(stock.get("name") or "").strip()
    query_market = str(stock.get("market") or "").strip().upper()
    title = first_text(raw, ("title", "reportTitle", "TITLE"))
    publish_time = first_text(raw, ("publishDate", "publishTime", "date", "PUBLISHDATE"))
    institution = first_text(raw, ("orgSName", "orgName", "institution", "ORG_S_NAME"))
    analyst = first_text(raw, ("researcher", "author", "analyst", "researcherName"))
    company = first_text(raw, ("stockName", "company", "securityName", "name"), query_name)
    symbol = first_text(raw, ("stockCode", "code", "securityCode", "symbol"), query_code)
    rating = first_text(raw, ("emRatingName", "ratingName", "rating", "rate"))
    summary = first_text(raw, ("summary", "abstract", "digest", "content"))

    url = first_text(raw, ("url", "reportUrl", "webUrl"))
    info_code = first_text(raw, ("infoCode", "info_code", "INFO_CODE"))
    if not url and info_code:
        url = f"https://data.eastmoney.com/report/zw_stock.jshtml?infocode={info_code}"

    return {
        "query_code": query_code,
        "query_name": query_name,
        "query_market": query_market,
        "title": title,
        "publish_time": publish_time[:10] if len(publish_time) >= 10 else publish_time,
        "institution": institution,
        "analyst": analyst,
        "company": company,
        "symbol": symbol,
        "rating": rating,
        "url": url,
        "summary": summary,
        "raw": raw,
    }


def fetch_stock_reports(stock: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    payload, errors = fetch_json(stock)
    if payload is None:
        return [], errors

    raw_items, item_errors = extract_raw_items(payload)
    errors.extend(item_errors)
    items = [normalize_item(item, stock) for item in raw_items]
    if not items:
        errors.append("No report items parsed from response")
    return items, errors


def build_result() -> dict[str, Any]:
    generated_at = now_local().isoformat()
    try:
        watchlist = load_watchlist(DEFAULT_WATCHLIST_PATH)
        watchlist_errors: list[str] = []
    except WatchlistError as exc:
        watchlist = []
        watchlist_errors = [str(exc)]

    if watchlist_errors:
        return {
            "source": SOURCE,
            "probe_name": PROBE_NAME,
            "generated_at": generated_at,
            "fetched_at": generated_at,
            "endpoint": ENDPOINT_BASE,
            "watchlist_path": DEFAULT_WATCHLIST_PATH.relative_to(PROJECT_ROOT).as_posix(),
            "watchlist_count": 0,
            "success_count": 0,
            "failed_count": 1,
            "success": False,
            "item_count": 0,
            "items": [],
            "failures": [{"code": "-", "name": "-", "market": "-", "errors": watchlist_errors}],
            "errors": watchlist_errors,
        }

    items: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for stock in watchlist:
        stock_items, errors = fetch_stock_reports(stock)
        if stock_items:
            items.extend(stock_items)
        if errors:
            failures.append(
                {
                    "code": stock.get("code", ""),
                    "name": stock.get("name", ""),
                    "market": stock.get("market", ""),
                    "errors": errors,
                }
            )

    success_count = len(watchlist) - len(failures)
    errors = [
        f"{failure['code']} {failure['name']}: {'; '.join(str(error) for error in failure['errors'])}"
        for failure in failures
    ]

    return {
        "source": SOURCE,
        "probe_name": PROBE_NAME,
        "generated_at": generated_at,
        "fetched_at": generated_at,
        "endpoint": ENDPOINT_BASE,
        "watchlist_path": DEFAULT_WATCHLIST_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "watchlist_count": len(watchlist),
        "success_count": success_count,
        "failed_count": len(failures),
        "success": bool(items) and success_count > 0,
        "item_count": len(items),
        "items": items,
        "failures": failures,
        "errors": errors,
    }


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


def upsert_probe_doc(result: dict[str, Any], raw_path: Path | None, latest_path: Path) -> None:
    doc_path = PROJECT_ROOT / "docs" / "endpoint_probe_results.md"
    existing = doc_path.read_text(encoding="utf-8") if doc_path.exists() else "# Endpoint Probe Results\n"
    marker = "## MVP2-003G Eastmoney Report Watchlist Probe"

    status = "Success" if result["success"] else "Failed"
    output_files = []
    if raw_path is not None:
        output_files.append(f"- {raw_path.relative_to(PROJECT_ROOT).as_posix()}")
    output_files.append(f"- {latest_path.relative_to(PROJECT_ROOT).as_posix()}")

    lines = [
        marker,
        "",
        f"Status: {status}",
        "",
        f"Checked time: {result['generated_at']}",
        "",
        f"Endpoint: {ENDPOINT_BASE}",
        "",
        "Method: GET",
        "",
        f"Watchlist path: {result['watchlist_path']}",
        f"Enabled watchlist count: {result['watchlist_count']}",
        f"Failed stock count: {result['failed_count']}",
        "",
        f"Request limit: {PAGE_SIZE} items per enabled stock, timeout {TIMEOUT_SECONDS}s",
        "",
        "Output files:",
        "",
        *output_files,
        "",
        "Observed fields:",
        "",
        "- query_code",
        "- query_name",
        "- query_market",
        "- title",
        "- publish_time",
        "- institution",
        "- analyst",
        "- company",
        "- symbol",
        "- rating",
        "- url",
        "- summary",
        "- raw",
        "",
        "Notes:",
        "",
        f"- Parsed {result['item_count']} item(s).",
        "- Reads enabled symbols from config/watchlist.json.",
        "- Uses the Eastmoney reportapi endpoint only.",
        "- Does not download report PDFs or parse full report text.",
        "- Rating, target price, and institution opinion fields are stored only as source metadata.",
        "- No evidence pack, report generation, LLM, or investment advice logic was changed.",
    ]

    if result["failures"]:
        lines.extend(["", "Failures:", ""])
        for failure in result["failures"]:
            joined = "; ".join(str(error) for error in failure["errors"])
            lines.append(f"- {failure.get('code')} {failure.get('name')} {failure.get('market')}: {joined}")

    doc_path.write_text(upsert_markdown_section(existing, marker, lines), encoding="utf-8")


def upsert_current_progress(result: dict[str, Any]) -> None:
    doc_path = PROJECT_ROOT / "docs" / "current_progress.md"
    existing = doc_path.read_text(encoding="utf-8") if doc_path.exists() else "# Current Progress\n"
    marker = "## MVP2-003G"
    status = "Completed" if result["success"] else "Failed"

    lines = [
        marker,
        "",
        f"Status: {status}",
        "",
        "Summary:",
        "",
        "- Upgraded the Eastmoney report probe to read enabled symbols from config/watchlist.json.",
        "- Added per-symbol query metadata fields: query_code, query_name, and query_market.",
        "- The probe records per-stock failures without crashing the whole batch.",
        "- Generated latest and dated Eastmoney report probe JSON.",
        "- No report PDF download, full-text parsing, LLM call, third-party dependency, evidence logic change, report logic change, or investment advice was added.",
        "- Rating, target price, and institution opinion fields remain source metadata only.",
        "",
        "Next:",
        "",
        "- MVP2 follow-up: adapt downstream evidence building only if multi-symbol report output needs additional compatibility.",
    ]

    if result["errors"]:
        lines.extend(["", "Errors:", ""])
        lines.extend(f"- {error}" for error in result["errors"])

    doc_path.write_text(upsert_markdown_section(existing, marker, lines), encoding="utf-8")


def write_probe_notes(result: dict[str, Any]) -> None:
    doc_path = PROJECT_ROOT / "docs" / "eastmoney_report_watchlist_probe_notes.md"
    lines = [
        "# Eastmoney Report Watchlist Probe Notes",
        "",
        "## Scope",
        "",
        "- Reads enabled symbols from `config/watchlist.json`.",
        "- Fetches Eastmoney research report metadata only.",
        "- Does not download report PDFs or parse full report text.",
        "- Does not call an LLM or generate investment advice.",
        "- Rating, target price, and institution opinion fields are retained only as source metadata.",
        "",
        "## Latest Verification",
        "",
        f"- Checked time: {result['generated_at']}",
        f"- Watchlist path: {result['watchlist_path']}",
        f"- Enabled stock count: {result['watchlist_count']}",
        f"- Report item count: {result['item_count']}",
        f"- Failed stock count: {result['failed_count']}",
        "",
        "## Output Metadata",
        "",
        "Each normalized item includes `query_code`, `query_name`, and `query_market` so downstream steps can trace which watchlist entry produced the report metadata.",
        "",
    ]
    if result["failures"]:
        lines.extend(["## Failures", ""])
        for failure in result["failures"]:
            joined = "; ".join(str(error) for error in failure["errors"])
            lines.append(f"- {failure.get('code')} {failure.get('name')} {failure.get('market')}: {joined}")
        lines.append("")

    doc_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    result = build_result()
    today = now_local().strftime("%Y%m%d")

    latest_path = PROJECT_ROOT / "data" / "cache" / "eastmoney_report_probe_latest.json"
    raw_path = PROJECT_ROOT / "data" / "raw" / f"eastmoney_report_probe_{today}.json"

    write_json(latest_path, result)
    saved_raw_path: Path | None = None
    if result["success"]:
        write_json(raw_path, result)
        saved_raw_path = raw_path

    upsert_probe_doc(result, saved_raw_path, latest_path)
    upsert_current_progress(result)
    write_probe_notes(result)

    print(f"Probe: {PROBE_NAME}")
    print(f"Endpoint: {ENDPOINT_BASE}")
    print("Method: GET")
    print(f"Watchlist path: {result['watchlist_path']}")
    print(f"Enabled symbols: {result['watchlist_count']}")
    print(f"Success: {result['success']}")
    print(f"Item count: {result['item_count']}")
    print(f"Failed stock count: {result['failed_count']}")
    print(f"Latest output: {latest_path.relative_to(PROJECT_ROOT).as_posix()}")
    if saved_raw_path is not None:
        print(f"Raw output: {saved_raw_path.relative_to(PROJECT_ROOT).as_posix()}")
    if result["failures"]:
        print("Failures:")
        for failure in result["failures"]:
            joined = "; ".join(str(error) for error in failure["errors"])
            print(f"- {failure.get('code')} {failure.get('name')} {failure.get('market')}: {joined}")

    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
