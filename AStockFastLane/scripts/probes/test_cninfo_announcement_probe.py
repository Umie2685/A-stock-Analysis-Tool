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


SOURCE = "cninfo_announcement"
PROBE_NAME = "cninfo_announcement_probe"
ENDPOINT = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
TIMEOUT_SECONDS = 15
PAGE_SIZE = 10
LOCAL_TZ = timezone(timedelta(hours=8))

# From local a-stock-data SKILL.md: 688017 uses orgId 9900041602.
# Keeping it fixed avoids an extra orgId lookup endpoint in this minimal probe.
TEST_SYMBOL = "688017"
TEST_ORG_ID = "9900041602"


def now_local() -> datetime:
    return datetime.now(LOCAL_TZ)


def cninfo_time_to_date(value: Any) -> str:
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value / 1000, tz=LOCAL_TZ).strftime("%Y-%m-%d")
        except (OSError, OverflowError, ValueError):
            return str(value)
    return str(value or "")[:10]


def build_payload() -> dict[str, str]:
    return {
        "stock": f"{TEST_SYMBOL},{TEST_ORG_ID}",
        "tabName": "fulltext",
        "pageSize": str(PAGE_SIZE),
        "pageNum": "1",
        "column": "sse",
        "category": "",
        "plate": "sh",
        "seDate": "",
        "searchkey": "",
        "secid": "",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true",
    }


def fetch_json() -> tuple[dict[str, Any] | None, list[str]]:
    data = urlencode(build_payload()).encode("utf-8")
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


def normalize_item(raw: dict[str, Any]) -> dict[str, Any]:
    title = str(raw.get("announcementTitle") or raw.get("title") or "").strip()
    publish_time = cninfo_time_to_date(raw.get("announcementTime"))
    company = str(raw.get("secName") or raw.get("company") or "").strip()
    symbol = str(raw.get("secCode") or raw.get("symbol") or TEST_SYMBOL).strip()
    announcement_type = str(
        raw.get("announcementTypeName") or raw.get("category") or ""
    ).strip()
    announcement_id = str(raw.get("announcementId") or "").strip()
    org_id = str(raw.get("orgId") or TEST_ORG_ID).strip()

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
        "title": title,
        "publish_time": publish_time,
        "company": company,
        "symbol": symbol,
        "announcement_type": announcement_type,
        "url": url,
        "raw": raw,
    }


def extract_items(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    announcements = payload.get("announcements", [])
    if announcements is None:
        announcements = []

    if not isinstance(announcements, list):
        return [], ["Unexpected response: announcements is not a list"]

    rows = [item for item in announcements if isinstance(item, dict)]
    return [normalize_item(item) for item in rows[:PAGE_SIZE]], []


def build_result() -> dict[str, Any]:
    fetched_at = now_local().isoformat()
    payload, errors = fetch_json()
    items: list[dict[str, Any]] = []

    if payload is not None:
        if "announcements" not in payload:
            errors.append("Unexpected response: announcements field missing")
        items, item_errors = extract_items(payload)
        errors.extend(item_errors)
        if not items:
            errors.append("No announcement items parsed from response")

    return {
        "source": SOURCE,
        "probe_name": PROBE_NAME,
        "fetched_at": fetched_at,
        "endpoint": ENDPOINT,
        "success": bool(items) and not errors,
        "item_count": len(items),
        "items": items,
        "errors": errors,
    }


def upsert_probe_doc(result: dict[str, Any], raw_path: Path | None, latest_path: Path) -> None:
    doc_path = PROJECT_ROOT / "docs" / "endpoint_probe_results.md"
    existing = doc_path.read_text(encoding="utf-8") if doc_path.exists() else "# Endpoint Probe Results\n"
    marker = "## MVP0-007G CNInfo Announcement Probe"
    before = existing.split(marker, 1)[0].rstrip()

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
        f"Checked time: {result['fetched_at']}",
        "",
        f"Endpoint: {ENDPOINT}",
        "",
        f"Method: POST",
        "",
        f"Request limit: {PAGE_SIZE} items, 1 request, timeout {TIMEOUT_SECONDS}s",
        "",
        f"Probe stock: {TEST_SYMBOL}",
        "",
        "Output files:",
        "",
        *output_files,
        "",
        "Observed fields:",
        "",
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
        "- Uses one CNInfo announcement endpoint only.",
        "- Does not download announcement PDFs.",
        "- No provider, pipeline, evidence pack, or report was generated.",
    ]

    if result["errors"]:
        lines.extend(["", "Failure reason:", ""])
        lines.extend(f"- {error}" for error in result["errors"])

    doc_path.write_text(f"{before}\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def upsert_current_progress(result: dict[str, Any]) -> None:
    doc_path = PROJECT_ROOT / "docs" / "current_progress.md"
    existing = doc_path.read_text(encoding="utf-8") if doc_path.exists() else "# Current Progress\n"
    marker = "## MVP0-007G"
    before = existing.split(marker, 1)[0].rstrip()
    status = "Completed" if result["success"] else "Failed"

    lines = [
        marker,
        "",
        f"Status: {status}",
        "",
        "Summary:",
        "",
        "- Confirmed one CNInfo announcement endpoint from local a-stock-data SKILL.md.",
        "- Implemented CNInfo announcement minimal probe.",
        "- Generated raw/cache announcement JSON.",
        "- No PDF download, Evidence Pack generation, report generation, or investment advice was produced.",
        "",
        "Next:",
        "",
        "- MVP0-008G: Merge CNInfo announcements into Fast Evidence Pack.",
    ]

    if result["errors"]:
        lines.extend(["", "Errors:", ""])
        lines.extend(f"- {error}" for error in result["errors"])

    doc_path.write_text(f"{before}\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


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

    print(f"Probe: {PROBE_NAME}")
    print(f"Endpoint: {ENDPOINT}")
    print("Method: POST")
    print(f"Success: {result['success']}")
    print(f"Item count: {result['item_count']}")
    print(f"Latest output: {latest_path.relative_to(PROJECT_ROOT).as_posix()}")
    if saved_raw_path is not None:
        print(f"Raw output: {saved_raw_path.relative_to(PROJECT_ROOT).as_posix()}")
    if result["errors"]:
        print("Errors:")
        for error in result["errors"]:
            print(f"- {error}")

    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

