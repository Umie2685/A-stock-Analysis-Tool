from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone, timedelta
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


SOURCE = "eastmoney_news"
PROBE_NAME = "eastmoney_news_probe"
ENDPOINT_BASE = "https://np-weblist.eastmoney.com/comm/web/getFastNewsList"
PAGE_SIZE = 10
TIMEOUT_SECONDS = 10
LOCAL_TZ = timezone(timedelta(hours=8))


def now_local() -> datetime:
    return datetime.now(LOCAL_TZ)


def build_endpoint() -> str:
    params = {
        "client": "web",
        "biz": "web_724",
        "fastColumn": "102",
        "sortEnd": "",
        "pageSize": str(PAGE_SIZE),
        "req_trace": f"astockfastlane-{uuid.uuid4().hex}",
    }
    return f"{ENDPOINT_BASE}?{urlencode(params)}"


def fetch_json(endpoint: str) -> tuple[dict[str, Any] | None, list[str]]:
    request = Request(
        endpoint,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0 Safari/537.36"
            ),
            "Referer": "https://kuaixun.eastmoney.com/",
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
    errors: list[str] = []
    data = payload.get("data")
    if not isinstance(data, dict):
        return [], ["Unexpected response: data is missing or not an object"]

    candidates = [
        data.get("fastNewsList"),
        data.get("list"),
        data.get("items"),
        data.get("news"),
    ]

    for candidate in candidates:
        if isinstance(candidate, list):
            rows = [item for item in candidate if isinstance(item, dict)]
            return rows[:PAGE_SIZE], errors

    return [], ["Unexpected response: no supported news list field found"]


def normalize_item(raw: dict[str, Any]) -> dict[str, Any]:
    title = str(raw.get("title") or raw.get("newsTitle") or "").strip()
    publish_time = str(
        raw.get("showTime")
        or raw.get("publishTime")
        or raw.get("time")
        or raw.get("date")
        or ""
    ).strip()
    source = str(raw.get("source") or raw.get("mediaName") or "eastmoney").strip()
    summary = str(raw.get("summary") or raw.get("digest") or raw.get("content") or "").strip()

    url = str(raw.get("url") or raw.get("arturl") or raw.get("link") or "").strip()
    code = str(raw.get("code") or "").strip()
    if not url and code:
        url = f"https://finance.eastmoney.com/a/{code}.html"

    return {
        "title": title,
        "publish_time": publish_time,
        "source": source or "eastmoney",
        "url": url,
        "summary": summary,
        "raw": raw,
    }


def build_result() -> dict[str, Any]:
    fetched_at = now_local()
    endpoint = build_endpoint()
    payload, errors = fetch_json(endpoint)
    items: list[dict[str, Any]] = []

    if payload is not None:
        code = str(payload.get("code", ""))
        message = str(payload.get("message", ""))
        if code not in {"1", "0"} or message.lower() not in {"success", ""}:
            errors.append(f"Endpoint returned code={code!r} message={message!r}")

        raw_items, item_errors = extract_raw_items(payload)
        errors.extend(item_errors)
        items = [normalize_item(item) for item in raw_items]

        if not items:
            errors.append("No news items parsed from response")

    return {
        "source": SOURCE,
        "probe_name": PROBE_NAME,
        "fetched_at": fetched_at.isoformat(),
        "endpoint": endpoint,
        "success": bool(items) and not errors,
        "item_count": len(items),
        "items": items,
        "errors": errors,
    }


def upsert_probe_doc(result: dict[str, Any], raw_path: Path | None, latest_path: Path) -> None:
    doc_path = PROJECT_ROOT / "docs" / "endpoint_probe_results.md"
    existing = doc_path.read_text(encoding="utf-8") if doc_path.exists() else "# Endpoint Probe Results\n"

    marker = "## MVP0-003 Eastmoney News Probe"
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
        f"Endpoint: {result['endpoint']}",
        "",
        f"Request limit: {PAGE_SIZE} items, 1 request, timeout {TIMEOUT_SECONDS}s",
        "",
        "Output files:",
        "",
        *output_files,
        "",
        "Observed fields:",
        "",
        "- title",
        "- publish_time",
        "- source",
        "- url",
        "- summary",
        "- raw",
        "",
        "Notes:",
        "",
        f"- Parsed {result['item_count']} item(s).",
        "- Uses one Eastmoney global 7x24 fast-news endpoint only.",
        "- No provider, pipeline, evidence pack, or report was generated.",
    ]

    if result["errors"]:
        lines.extend(["", "Failure reason:", ""])
        lines.extend(f"- {error}" for error in result["errors"])

    doc_path.write_text(f"{before}\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    result = build_result()
    today = now_local().strftime("%Y%m%d")

    latest_path = PROJECT_ROOT / "data" / "cache" / "eastmoney_news_probe_latest.json"
    raw_path = PROJECT_ROOT / "data" / "raw" / f"eastmoney_news_probe_{today}.json"

    write_json(latest_path, result)
    saved_raw_path: Path | None = None
    if result["success"]:
        write_json(raw_path, result)
        saved_raw_path = raw_path

    upsert_probe_doc(result, saved_raw_path, latest_path)

    print(f"Probe: {PROBE_NAME}")
    print(f"Endpoint: {result['endpoint']}")
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
