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


SOURCE = "cninfo_announcement"
PROBE_NAME = "cninfo_announcement_probe"
ENDPOINT = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
TIMEOUT_SECONDS = 15
PAGE_SIZE = 10
LOCAL_TZ = timezone(timedelta(hours=8))


def now_local() -> datetime:
    return datetime.now(LOCAL_TZ)


def cninfo_time_to_date(value: Any) -> str:
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value / 1000, tz=LOCAL_TZ).strftime("%Y-%m-%d")
        except (OSError, OverflowError, ValueError):
            return str(value)
    return str(value or "")[:10]


def cninfo_plate(market: str) -> str:
    normalized = market.upper()
    if normalized == "SH":
        return "sh"
    if normalized == "SZ":
        return "sz"
    if normalized == "BJ":
        return "bj"
    return ""


def cninfo_column(market: str) -> str:
    normalized = market.upper()
    if normalized == "SH":
        return "sse"
    if normalized == "SZ":
        return "szse"
    if normalized == "BJ":
        return "bj"
    return ""


def read_watchlist_payload(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def load_probe_watchlist() -> tuple[list[dict[str, Any]], list[str]]:
    try:
        enabled_items = load_watchlist(DEFAULT_WATCHLIST_PATH)
    except WatchlistError as exc:
        return [], [str(exc)]

    raw_payload = read_watchlist_payload(DEFAULT_WATCHLIST_PATH)
    raw_items = raw_payload.get("items", [])
    org_id_by_code: dict[str, str] = {}
    if isinstance(raw_items, list):
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            code = str(item.get("code") or "").strip()
            org_id = str(item.get("orgId") or item.get("org_id") or "").strip()
            if code and org_id:
                org_id_by_code[code] = org_id

    merged: list[dict[str, Any]] = []
    for item in enabled_items:
        item_with_org = dict(item)
        item_with_org["orgId"] = org_id_by_code.get(item["code"], "")
        merged.append(item_with_org)
    return merged, []


def build_payload(stock: dict[str, Any]) -> dict[str, str]:
    code = str(stock["code"])
    org_id = str(stock.get("orgId") or "").strip()
    stock_param = f"{code},{org_id}" if org_id else code
    market = str(stock.get("market") or "")

    return {
        "stock": stock_param,
        "tabName": "fulltext",
        "pageSize": str(PAGE_SIZE),
        "pageNum": "1",
        "column": cninfo_column(market),
        "category": "",
        "plate": cninfo_plate(market),
        "seDate": "",
        "searchkey": "",
        "secid": "",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true",
    }


def fetch_json(stock: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    data = urlencode(build_payload(stock)).encode("utf-8")
    request = Request(
        ENDPOINT,
        data=data,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0 Safari/537.36"
            ),
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json,text/plain,*/*",
            "Origin": "https://www.cninfo.com.cn",
            "Referer": "https://www.cninfo.com.cn/new/disclosure",
        },
        method="POST",
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


def normalize_item(raw: dict[str, Any], stock: dict[str, Any]) -> dict[str, Any]:
    query_code = str(stock.get("code") or "").strip()
    query_name = str(stock.get("name") or "").strip()
    query_market = str(stock.get("market") or "").strip().upper()
    title = str(raw.get("announcementTitle") or raw.get("title") or "").strip()
    publish_time = cninfo_time_to_date(raw.get("announcementTime"))
    company = str(raw.get("secName") or raw.get("company") or query_name).strip()
    symbol = str(raw.get("secCode") or raw.get("symbol") or query_code).strip()
    announcement_type = str(
        raw.get("announcementTypeName") or raw.get("category") or raw.get("announcementType") or ""
    ).strip()
    announcement_id = str(raw.get("announcementId") or "").strip()
    org_id = str(raw.get("orgId") or stock.get("orgId") or "").strip()

    if announcement_id:
        url = (
            "https://www.cninfo.com.cn/new/disclosure/detail"
            f"?stockCode={symbol}&announcementId={announcement_id}"
            f"&orgId={org_id}&announcementTime={publish_time}"
        )
    else:
        adjunct_url = str(raw.get("adjunctUrl") or "").strip()
        url = f"https://static.cninfo.com.cn/{adjunct_url}" if adjunct_url else ""

    return {
        "query_code": query_code,
        "query_name": query_name,
        "query_market": query_market,
        "query_orgId": str(stock.get("orgId") or "").strip(),
        "title": title,
        "publish_time": publish_time,
        "company": company,
        "symbol": symbol,
        "announcement_type": announcement_type,
        "url": url,
        "raw": raw,
    }


def extract_items(payload: dict[str, Any], stock: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    announcements = payload.get("announcements", [])
    if announcements is None:
        announcements = []

    if not isinstance(announcements, list):
        return [], ["Unexpected response: announcements is not a list"]

    rows = [item for item in announcements if isinstance(item, dict)]
    return [normalize_item(item, stock) for item in rows[:PAGE_SIZE]], []


def fetch_stock_announcements(stock: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    payload, errors = fetch_json(stock)
    if payload is None:
        return [], errors

    if "announcements" not in payload:
        errors.append("Unexpected response: announcements field missing")

    items, item_errors = extract_items(payload, stock)
    errors.extend(item_errors)
    if not items:
        errors.append("No announcement items parsed from response")
    return items, errors


def stock_display(stock: dict[str, Any]) -> str:
    org_id = str(stock.get("orgId") or "-")
    return f"{stock.get('code')} {stock.get('name')} {stock.get('market')} orgId={org_id}"


def build_result() -> dict[str, Any]:
    generated_at = now_local().isoformat()
    watchlist, watchlist_errors = load_probe_watchlist()
    items: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    if watchlist_errors:
        return {
            "source": SOURCE,
            "probe_name": PROBE_NAME,
            "generated_at": generated_at,
            "fetched_at": generated_at,
            "endpoint": ENDPOINT,
            "watchlist_path": DEFAULT_WATCHLIST_PATH.relative_to(PROJECT_ROOT).as_posix(),
            "watchlist_count": 0,
            "success_count": 0,
            "failed_count": 1,
            "success": False,
            "item_count": 0,
            "items": [],
            "failures": [{"code": "-", "name": "-", "market": "-", "orgId": "-", "errors": watchlist_errors}],
            "errors": watchlist_errors,
        }

    for stock in watchlist:
        stock_items, errors = fetch_stock_announcements(stock)
        if stock_items:
            items.extend(stock_items)
        if errors:
            failures.append(
                {
                    "code": stock.get("code", ""),
                    "name": stock.get("name", ""),
                    "market": stock.get("market", ""),
                    "orgId": stock.get("orgId", ""),
                    "errors": errors,
                }
            )

    success_count = len(watchlist) - len(failures)
    failed_count = len(failures)
    errors = [
        f"{failure['code']} {failure['name']}: {'; '.join(str(error) for error in failure['errors'])}"
        for failure in failures
    ]

    return {
        "source": SOURCE,
        "probe_name": PROBE_NAME,
        "generated_at": generated_at,
        "fetched_at": generated_at,
        "endpoint": ENDPOINT,
        "watchlist_path": DEFAULT_WATCHLIST_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "watchlist_count": len(watchlist),
        "success_count": success_count,
        "failed_count": failed_count,
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
    marker = "## MVP2-002G CNInfo Watchlist Announcement Probe"

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
        f"Endpoint: {ENDPOINT}",
        "",
        "Method: POST",
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
        "- company",
        "- symbol",
        "- announcement_type",
        "- url",
        "- raw",
        "",
        "Notes:",
        "",
        f"- Parsed {result['item_count']} item(s).",
        "- Reads enabled symbols from config/watchlist.json.",
        "- Uses the CNInfo announcement endpoint only.",
        "- Does not download or parse announcement PDFs.",
        "- No provider, evidence pack, report, LLM, or investment advice logic was generated.",
    ]

    if result["failures"]:
        lines.extend(["", "Failures:", ""])
        for failure in result["failures"]:
            joined = "; ".join(str(error) for error in failure["errors"])
            lines.append(
                f"- {failure.get('code')} {failure.get('name')} {failure.get('market')} "
                f"orgId={failure.get('orgId') or '-'}: {joined}"
            )

    doc_path.write_text(upsert_markdown_section(existing, marker, lines), encoding="utf-8")


def upsert_current_progress(result: dict[str, Any]) -> None:
    doc_path = PROJECT_ROOT / "docs" / "current_progress.md"
    existing = doc_path.read_text(encoding="utf-8") if doc_path.exists() else "# Current Progress\n"
    marker = "## MVP2-002G"
    status = "Completed" if result["success"] else "Failed"

    lines = [
        marker,
        "",
        f"Status: {status}",
        "",
        "Summary:",
        "",
        "- Upgraded the CNInfo announcement probe to read enabled symbols from config/watchlist.json.",
        "- Added per-symbol query metadata fields: query_code, query_name, query_market, and query_orgId.",
        "- The probe records per-stock failures without crashing the whole batch.",
        "- Generated latest and dated CNInfo announcement probe JSON.",
        "- No announcement PDF download, PDF parsing, LLM call, third-party dependency, evidence logic change, report logic change, or investment advice was added.",
        "",
        "Next:",
        "",
        "- MVP2 follow-up: adapt downstream evidence building only if multi-symbol output needs additional compatibility.",
    ]

    if result["errors"]:
        lines.extend(["", "Errors:", ""])
        lines.extend(f"- {error}" for error in result["errors"])

    doc_path.write_text(upsert_markdown_section(existing, marker, lines), encoding="utf-8")


def write_probe_notes(result: dict[str, Any]) -> None:
    doc_path = PROJECT_ROOT / "docs" / "cninfo_watchlist_probe_notes.md"
    lines = [
        "# CNInfo Watchlist Announcement Probe Notes",
        "",
        "## Scope",
        "",
        "- Reads enabled symbols from `config/watchlist.json`.",
        "- Fetches CNInfo announcement metadata only.",
        "- Does not download or parse PDF files.",
        "- Does not call an LLM or generate investment advice.",
        "",
        "## Latest Verification",
        "",
        f"- Checked time: {result['generated_at']}",
        f"- Watchlist path: {result['watchlist_path']}",
        f"- Enabled stock count: {result['watchlist_count']}",
        f"- Announcement item count: {result['item_count']}",
        f"- Failed stock count: {result['failed_count']}",
        "",
        "## Output Metadata",
        "",
        "Each normalized item includes `query_code`, `query_name`, `query_market`, and `query_orgId` so downstream steps can trace which watchlist entry produced the announcement.",
        "",
    ]
    if result["failures"]:
        lines.extend(["## Failures", ""])
        for failure in result["failures"]:
            joined = "; ".join(str(error) for error in failure["errors"])
            lines.append(
                f"- {failure.get('code')} {failure.get('name')} {failure.get('market')} "
                f"orgId={failure.get('orgId') or '-'}: {joined}"
            )
        lines.append("")

    doc_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    result = build_result()
    today = now_local().strftime("%Y%m%d")

    latest_path = PROJECT_ROOT / "data" / "cache" / "cninfo_announcement_probe_latest.json"
    raw_path = PROJECT_ROOT / "data" / "raw" / f"cninfo_announcement_probe_{today}.json"

    write_json(latest_path, result)
    saved_raw_path: Path | None = None
    if result["success"]:
        write_json(raw_path, result)
        saved_raw_path = raw_path

    upsert_probe_doc(result, saved_raw_path, latest_path)
    upsert_current_progress(result)
    write_probe_notes(result)

    print(f"Probe: {PROBE_NAME}")
    print(f"Endpoint: {ENDPOINT}")
    print("Method: POST")
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
            print(
                f"- {failure.get('code')} {failure.get('name')} {failure.get('market')} "
                f"orgId={failure.get('orgId') or '-'}: {joined}"
            )

    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
