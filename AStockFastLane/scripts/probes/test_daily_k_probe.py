from __future__ import annotations

import argparse
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


SOURCE = "tencent_daily_k"
PROBE_NAME = "daily_k_probe"
CANDIDATE_PATH = PROJECT_ROOT / "data" / "analysis" / "candidate_watchlist_latest.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "market"
LATEST_PATH = OUTPUT_DIR / "daily_k_latest.json"
ENDPOINT_BASE = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
TIMEOUT_SECONDS = 15
DEFAULT_LIMIT = 10
DEFAULT_DAYS = 60
DEFAULT_ADJUST_TYPE = "none"
LOCAL_TZ = timezone(timedelta(hours=8))


def now_local() -> datetime:
    return datetime.now(LOCAL_TZ)


def text_value(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def normalize_code(value: Any) -> str:
    raw = text_value(value)
    if "." in raw:
        first, second = raw.split(".", 1)
        raw = first if first.isdigit() else second
    raw = raw.lower().removeprefix("sh").removeprefix("sz").removeprefix("bj")
    digits = "".join(ch for ch in raw if ch.isdigit())
    return digits.zfill(6) if 0 < len(digits) <= 6 else digits


def infer_market(code: str) -> str | None:
    if code.startswith(("600", "601", "603", "605", "688")):
        return "SH"
    if code.startswith(("000", "001", "002", "003", "300", "301")):
        return "SZ"
    if code.startswith(("8", "4", "9")) and len(code) == 6:
        return "BJ"
    return None


def tencent_symbol(code: str, market: str) -> str | None:
    if market == "SH":
        return f"sh{code}"
    if market == "SZ":
        return f"sz{code}"
    return None


def load_candidates(path: Path, limit: int) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], [f"Candidate file not found: {path.relative_to(PROJECT_ROOT).as_posix()}"]

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], [f"Candidate file JSONDecodeError: {exc}"]
    except OSError as exc:
        return [], [f"Candidate file read failed: {exc}"]

    if not isinstance(payload, dict):
        return [], ["Candidate file root is not an object"]

    raw_candidates = payload.get("candidates")
    if not isinstance(raw_candidates, list):
        return [], ["Candidate file field 'candidates' is missing or not a list"]

    candidates: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_candidates, start=1):
        if not isinstance(raw, dict):
            continue
        code = normalize_code(raw.get("code"))
        if not code:
            continue
        candidates.append(
            {
                "rank": index,
                "code": code,
                "name": text_value(raw.get("name")),
                "heat_score": raw.get("heat_score"),
                "related_concepts": raw.get("related_concepts")
                if isinstance(raw.get("related_concepts"), list)
                else [],
            }
        )
        if len(candidates) >= limit:
            break

    if not candidates:
        return [], ["Candidate file contains no usable candidate rows"]

    return candidates, []


def build_endpoint(symbol: str, days: int, adjust_type: str) -> str:
    if adjust_type == "qfq":
        kline_type = "qfqday"
    elif adjust_type == "hfq":
        kline_type = "hfqday"
    else:
        kline_type = "day"
    fq_param = "" if adjust_type == "none" else adjust_type
    params = {
        "_var": "kline_day",
        "param": f"{symbol},{kline_type},,,{days},{fq_param}",
    }
    return f"{ENDPOINT_BASE}?{urlencode(params)}"


def fetch_tencent_daily_k(symbol: str, days: int, adjust_type: str) -> tuple[dict[str, Any] | None, str | None]:
    endpoint = build_endpoint(symbol, days, adjust_type)
    request = Request(
        endpoint,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0 Safari/537.36"
            ),
            "Referer": "https://gu.qq.com/",
            "Accept": "application/json,text/plain,*/*",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        return None, f"HTTPError: status={exc.code} reason={exc.reason}"
    except URLError as exc:
        return None, f"URLError: {exc.reason}"
    except TimeoutError as exc:
        return None, f"TimeoutError: {exc}"
    except OSError as exc:
        return None, f"OSError: {exc}"

    marker = "="
    if marker in body:
        body = body.split(marker, 1)[1].strip()
    body = body.rstrip(";")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        return None, f"JSONDecodeError: {exc}"

    if not isinstance(payload, dict):
        return None, "Unexpected JSON root: expected object"
    return payload, None


def number_or_none(value: Any) -> float | int | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed.is_integer():
        return int(parsed)
    return parsed


def normalize_bar(raw: list[Any]) -> dict[str, Any]:
    return {
        "trade_date": text_value(raw[0]) if len(raw) > 0 else "",
        "open": number_or_none(raw[1] if len(raw) > 1 else None),
        "close": number_or_none(raw[2] if len(raw) > 2 else None),
        "high": number_or_none(raw[3] if len(raw) > 3 else None),
        "low": number_or_none(raw[4] if len(raw) > 4 else None),
        "volume": number_or_none(raw[5] if len(raw) > 5 else None),
        "amount": number_or_none(raw[6] if len(raw) > 6 else None),
        "pct_chg": number_or_none(raw[8] if len(raw) > 8 else None),
        "turnover": None,
    }


def extract_bars(payload: dict[str, Any], symbol: str, adjust_type: str) -> tuple[list[dict[str, Any]], str | None]:
    data = payload.get("data")
    if not isinstance(data, dict):
        return [], "Unexpected response: data is missing or not an object"
    stock_data = data.get(symbol)
    if not isinstance(stock_data, dict):
        return [], f"Unexpected response: data.{symbol} is missing or not an object"

    raw_bars = None
    for key in ("day", "qfqday", "hfqday"):
        if isinstance(stock_data.get(key), list):
            raw_bars = stock_data.get(key)
            break
    if raw_bars is None:
        qt = stock_data.get("qt")
        if isinstance(qt, dict):
            code = str(stock_data.get("code") or "")
            if isinstance(qt.get(code), list):
                raw_bars = qt.get(code)

    if not isinstance(raw_bars, list):
        return [], f"Unexpected response: no daily k list found for adjust_type={adjust_type}"

    bars = [normalize_bar(row) for row in raw_bars if isinstance(row, list)]
    return bars, None


def empty_item(
    candidate: dict[str, Any],
    market: str | None,
    status: str,
    error: str,
    created_at: str,
    adjust_type: str,
) -> dict[str, Any]:
    return {
        "code": candidate["code"],
        "name": candidate.get("name", ""),
        "market": market or "",
        "query_code": candidate["code"],
        "query_name": candidate.get("name", ""),
        "source": SOURCE,
        "adjust_type": adjust_type,
        "data_status": status,
        "error_message": error,
        "bars": [],
        "created_at": created_at,
        "candidate_rank": candidate.get("rank"),
        "heat_score": candidate.get("heat_score"),
        "related_concepts": candidate.get("related_concepts", []),
    }


def fetch_candidate(candidate: dict[str, Any], days: int, adjust_type: str, created_at: str) -> dict[str, Any]:
    code = candidate["code"]
    market = infer_market(code)
    if market is None:
        return empty_item(candidate, market, "unsupported_market", f"Unsupported market for code={code}", created_at, adjust_type)

    symbol = tencent_symbol(code, market)
    if symbol is None:
        return empty_item(candidate, market, "unsupported_market", f"{market} market is not supported by this probe", created_at, adjust_type)

    payload, fetch_error = fetch_tencent_daily_k(symbol, days, adjust_type)
    if fetch_error:
        return empty_item(candidate, market, "fetch_failed", fetch_error, created_at, adjust_type)
    if payload is None:
        return empty_item(candidate, market, "fetch_failed", "Empty response payload", created_at, adjust_type)
    if str(payload.get("code")) != "0":
        return empty_item(
            candidate,
            market,
            "fetch_failed",
            f"Provider returned code={payload.get('code')!r} msg={payload.get('msg')!r}",
            created_at,
            adjust_type,
        )

    bars, parse_error = extract_bars(payload, symbol, adjust_type)
    if parse_error:
        return empty_item(candidate, market, "parse_failed", parse_error, created_at, adjust_type)
    if not bars:
        return empty_item(candidate, market, "empty_bars", "No daily K bars parsed from response", created_at, adjust_type)

    status = "ok"
    error_message = ""
    if len(bars) < 20:
        status = "insufficient_history"
        error_message = f"Only {len(bars)} daily K bars parsed; minimum is 20"

    return {
        "code": code,
        "name": candidate.get("name", ""),
        "market": market,
        "query_code": code,
        "query_name": candidate.get("name", ""),
        "source": SOURCE,
        "adjust_type": adjust_type,
        "data_status": status,
        "error_message": error_message,
        "bars": bars,
        "created_at": created_at,
        "candidate_rank": candidate.get("rank"),
        "heat_score": candidate.get("heat_score"),
        "related_concepts": candidate.get("related_concepts", []),
    }


def build_result(limit: int, days: int, source: str, adjust_type: str) -> dict[str, Any]:
    created_at = now_local().isoformat()
    candidates, input_errors = load_candidates(CANDIDATE_PATH, limit)

    items: list[dict[str, Any]] = []
    if source != "tencent":
        input_errors.append(f"Unsupported source={source!r}; only 'tencent' is implemented")
    elif candidates:
        for candidate in candidates:
            items.append(fetch_candidate(candidate, days, adjust_type, created_at))

    ok_count = sum(1 for item in items if item.get("data_status") == "ok")
    failed_count = len(items) - ok_count

    if input_errors and not items:
        failed_count = 0

    return {
        "meta": {
            "label": "daily_k",
            "probe_name": PROBE_NAME,
            "created_at": created_at,
            "source": SOURCE if source == "tencent" else source,
            "source_candidate_watchlist": CANDIDATE_PATH.relative_to(PROJECT_ROOT).as_posix(),
            "limit": limit,
            "days": days,
            "item_count": len(items),
            "ok_count": ok_count,
            "failed_count": failed_count,
            "adjust_type": adjust_type,
            "note": "low frequency daily k data for MVP4 trend analysis",
            "disclaimer": "仅用于公开信息整理和研究辅助，不构成投资建议、交易建议或交易信号，不承诺任何回报。",
        },
        "items": items,
        "errors": input_errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch low-frequency daily K data for candidate watchlist stocks.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Maximum candidate count to fetch, default 10.")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help="Daily K bar count to request, default 60.")
    parser.add_argument("--source", default="tencent", choices=["tencent"], help="Daily K source, default tencent.")
    parser.add_argument(
        "--adjust-type",
        default=DEFAULT_ADJUST_TYPE,
        choices=["none", "qfq", "hfq"],
        help="Adjustment type, default none.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    limit = max(1, args.limit)
    days = max(1, args.days)
    result = build_result(limit=limit, days=days, source=args.source, adjust_type=args.adjust_type)

    today = now_local().strftime("%Y%m%d")
    dated_path = OUTPUT_DIR / f"daily_k_{today}.json"
    write_json(LATEST_PATH, result)
    write_json(dated_path, result)

    meta = result["meta"]
    print("Daily K probe: daily_k")
    print(f"Source: {meta['source']}")
    print(f"Input: {meta['source_candidate_watchlist']}")
    print(f"Limit: {meta['limit']}")
    print(f"Days: {meta['days']}")
    print(f"Items: {meta['item_count']}")
    print(f"OK: {meta['ok_count']}")
    print(f"Failed: {meta['failed_count']}")
    print(f"Latest output: {LATEST_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Dated output: {dated_path.relative_to(PROJECT_ROOT).as_posix()}")
    if result.get("errors"):
        print("Errors:")
        for error in result["errors"]:
            print(f"- {error}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
