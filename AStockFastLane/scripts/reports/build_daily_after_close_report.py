from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOT_EVENTS_PATH = PROJECT_ROOT / "data" / "analysis" / "hot_events_latest.json"
CANDIDATE_WATCHLIST_PATH = PROJECT_ROOT / "data" / "analysis" / "candidate_watchlist_latest.json"
TREND_ANALYSIS_PATH = PROJECT_ROOT / "data" / "analysis" / "trend_analysis_latest.json"
CANDIDATE_REVIEW_PATH = PROJECT_ROOT / "data" / "analysis" / "candidate_review_latest.json"
CANDIDATE_REVIEW_STATUS_PATH = PROJECT_ROOT / "data" / "manual" / "candidate_review_status.json"
DAILY_JSON_LATEST_PATH = PROJECT_ROOT / "data" / "analysis" / "daily_after_close_report_latest.json"
DAILY_MD_LATEST_PATH = PROJECT_ROOT / "reports" / "daily_after_close_report_latest.md"
ALLOWED_STATUS = ["pending", "watch", "skip", "confirmed", "rejected"]
TZ = timezone(timedelta(hours=8))
DISCLAIMER = "研究辅助，不构成投资建议。"


def now_text() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def today_stamp() -> str:
    return datetime.now(TZ).strftime("%Y%m%d")


def read_json(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, f"missing: {relative_path(path)}"
    except json.JSONDecodeError as exc:
        return {}, f"json decode failed: {relative_path(path)}: {exc}"
    except OSError as exc:
        return {}, f"read failed: {relative_path(path)}: {exc}"
    if not isinstance(payload, dict):
        return {}, f"json root is not an object: {relative_path(path)}"
    return payload, None


def relative_path(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def text_value(value: Any, fallback: str = "-") -> str:
    if value is None:
        return fallback
    if isinstance(value, list):
        parts = [text_value(item, "") for item in value]
        text = "、".join(part for part in parts if part)
        return text or fallback
    if isinstance(value, dict):
        return text_value(list(value.values()), fallback)
    text = str(value).strip()
    return text or fallback


def list_items(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    items = payload.get(key, [])
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def status_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return list_items(payload, "items")


def build_status_index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for item in status_items(payload):
        code = text_value(item.get("code"), "")
        if not code:
            continue
        current = index.get(code)
        updated_at = text_value(item.get("updated_at"), "")
        current_updated_at = text_value(current.get("updated_at"), "") if current else ""
        if current is None or updated_at >= current_updated_at:
            index[code] = item
    return index


def manual_status_for(code: Any, status_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    item = status_index.get(text_value(code, ""), {})
    status = text_value(item.get("status"), "pending")
    if status not in ALLOWED_STATUS:
        status = "pending"
    confirmed = item.get("confirmed_by_user")
    return {
        "manual_status": status,
        "confirmed_by_user": confirmed if isinstance(confirmed, bool) else False,
        "review_note": text_value(item.get("review_note"), "-"),
        "status_updated_at": text_value(item.get("updated_at"), "-"),
    }


def impact_rank(value: Any) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(text_value(value, "unknown"), 3)


def concept_names(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    names: list[str] = []
    for value in values:
        if isinstance(value, dict):
            name = text_value(value.get("concept"), "")
        else:
            name = text_value(value, "")
        if name and name not in names:
            names.append(name)
    return names


def hot_mainlines(hot_payload: dict[str, Any]) -> list[dict[str, Any]]:
    events = list_items(hot_payload, "hot_events")
    rows: list[dict[str, Any]] = []
    for event in events:
        strength = text_value(event.get("impact_strength"), "unknown")
        if strength not in {"high", "medium"}:
            continue
        rows.append(
            {
                "title": text_value(event.get("title")),
                "impact_strength": strength,
                "impact_score": event.get("impact_score", 0),
                "related_concepts": concept_names(event.get("matched_concepts") or event.get("related_concepts") or []),
                "risk_notes": event.get("risk_notes") or [],
            }
        )
    rows.sort(key=lambda item: (impact_rank(item.get("impact_strength")), -float(item.get("impact_score") or 0)))
    return rows[:8]


def selected_candidates(review_payload: dict[str, Any], status_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in list_items(review_payload, "items"):
        if item.get("selected_for_review") is not True:
            continue
        status = manual_status_for(item.get("code"), status_index)
        rows.append(
            {
                "code": text_value(item.get("code")),
                "name": text_value(item.get("name")),
                "market": text_value(item.get("market")),
                "review_bucket": text_value(item.get("review_bucket")),
                "final_score": item.get("final_score", "-"),
                "trend_state": text_value(item.get("trend_state")),
                "bucket_reason": text_value(item.get("bucket_reason")),
                **status,
            }
        )
    return rows


def manual_status_summary(selected: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(text_value(item.get("manual_status"), "pending") for item in selected)
    return {status: counts.get(status, 0) for status in ALLOWED_STATUS}


def review_items_by_status(status_index: dict[str, dict[str, Any]], status: str) -> list[dict[str, Any]]:
    rows = []
    for item in status_index.values():
        if text_value(item.get("status"), "pending") == status:
            rows.append(
                {
                    "code": text_value(item.get("code")),
                    "name": text_value(item.get("name")),
                    "market": text_value(item.get("market")),
                    "review_bucket": text_value(item.get("review_bucket")),
                    "review_note": text_value(item.get("review_note")),
                    "updated_at": text_value(item.get("updated_at")),
                }
            )
    return sorted(rows, key=lambda item: (item.get("code", ""), item.get("updated_at", "")))


def wind_vane_table(review_payload: dict[str, Any], status_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    wanted = {"core_watch", "elastic_watch", "market_height_watch"}
    rows: list[dict[str, Any]] = []
    for item in list_items(review_payload, "items"):
        bucket = text_value(item.get("review_bucket"))
        if item.get("selected_for_review") is not True and bucket not in wanted:
            continue
        status = manual_status_for(item.get("code"), status_index)
        rows.append(
            {
                "code": text_value(item.get("code")),
                "name": text_value(item.get("name")),
                "layer": bucket,
                "trend_state": text_value(item.get("trend_state")),
                "manual_status": status["manual_status"],
                "focus_reason": text_value(item.get("bucket_reason")),
            }
        )
    return rows[:12]


def tomorrow_watch(mainlines: list[dict[str, Any]], selected: list[dict[str, Any]]) -> list[str]:
    points: list[str] = []
    for item in mainlines[:3]:
        points.append(f"跟踪主线热度是否延续：{text_value(item.get('title'))}。")
    for item in selected[:3]:
        points.append(
            f"人工确认 {text_value(item.get('name'))}({text_value(item.get('code'))}) 的状态与风险备注，当前状态为 {text_value(item.get('manual_status'), 'pending')}。"
        )
    if not points:
        points.append("继续观察热点、趋势与人工审核状态是否形成一致信号。")
    points.append("保持规则版记录，不自动写入 watchlist。")
    return points[:8]


def risk_notes(errors: list[str]) -> list[str]:
    notes = [
        "本报告仅整理公开信息和本地规则结果。",
        "人工状态需要用户自行确认，状态缺失时按 pending 展示。",
        "热点、趋势与候选池均可能随数据刷新而变化。",
    ]
    if errors:
        notes.append("部分输入文件存在读取问题，请先检查数据健康信息。")
    return notes


def market_summary(
    hot_payload: dict[str, Any],
    candidate_payload: dict[str, Any],
    trend_payload: dict[str, Any],
    review_payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "hot_event_count": hot_payload.get("event_count", len(list_items(hot_payload, "hot_events"))),
        "candidate_count": candidate_payload.get("candidate_count", len(list_items(candidate_payload, "candidates"))),
        "trend_item_count": trend_payload.get("meta", {}).get("item_count", len(list_items(trend_payload, "items"))),
        "candidate_review_count": review_payload.get("meta", {}).get("item_count", len(list_items(review_payload, "items"))),
        "selected_review_count": review_payload.get("meta", {}).get("selected_count", 0),
    }


def build_report() -> dict[str, Any]:
    created_at = now_text()
    inputs = [
        HOT_EVENTS_PATH,
        CANDIDATE_WATCHLIST_PATH,
        TREND_ANALYSIS_PATH,
        CANDIDATE_REVIEW_PATH,
        CANDIDATE_REVIEW_STATUS_PATH,
    ]
    payloads: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for path in inputs:
        payload, error = read_json(path)
        payloads[path.name] = payload
        if error:
            errors.append(error)

    status_index = build_status_index(payloads[CANDIDATE_REVIEW_STATUS_PATH.name])
    mainlines = hot_mainlines(payloads[HOT_EVENTS_PATH.name])
    selected = selected_candidates(payloads[CANDIDATE_REVIEW_PATH.name], status_index)
    summary = manual_status_summary(selected)
    report = {
        "meta": {
            "label": "daily_after_close_report",
            "method": "rule_based",
            "created_at": created_at,
            "disclaimer": DISCLAIMER,
            "input_files": [relative_path(path) for path in inputs],
        },
        "market_summary": market_summary(
            payloads[HOT_EVENTS_PATH.name],
            payloads[CANDIDATE_WATCHLIST_PATH.name],
            payloads[TREND_ANALYSIS_PATH.name],
            payloads[CANDIDATE_REVIEW_PATH.name],
        ),
        "hot_mainlines": mainlines,
        "selected_candidates": selected,
        "manual_status_summary": summary,
        "watch_items": review_items_by_status(status_index, "watch"),
        "confirmed_items": review_items_by_status(status_index, "confirmed"),
        "rejected_items": review_items_by_status(status_index, "rejected"),
        "wind_vane_table": wind_vane_table(payloads[CANDIDATE_REVIEW_PATH.name], status_index),
        "tomorrow_watch": tomorrow_watch(mainlines, selected),
        "risk_notes": risk_notes(errors),
        "errors": errors,
    }
    return report


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "- 暂无。\n"
    header = "| " + " | ".join(headers) + " |"
    line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = ["| " + " | ".join(text_value(cell) for cell in row) + " |" for row in rows]
    return "\n".join([header, line, *body]) + "\n"


def render_markdown(report: dict[str, Any]) -> str:
    meta = report.get("meta", {})
    mainline_rows = [
        [item.get("impact_strength"), item.get("impact_score"), item.get("title")]
        for item in report.get("hot_mainlines", [])
    ]
    selected_rows = [
        [
            item.get("code"),
            item.get("name"),
            item.get("review_bucket"),
            item.get("final_score"),
            item.get("trend_state"),
            item.get("manual_status"),
            item.get("review_note"),
        ]
        for item in report.get("selected_candidates", [])
    ]
    status_rows = [[key, value] for key, value in report.get("manual_status_summary", {}).items()]
    wind_rows = [
        [
            item.get("name"),
            item.get("code"),
            item.get("layer"),
            item.get("trend_state"),
            item.get("manual_status"),
            item.get("focus_reason"),
        ]
        for item in report.get("wind_vane_table", [])
    ]
    watch_points = "\n".join(f"- {text_value(item)}" for item in report.get("tomorrow_watch", []))
    risks = "\n".join(f"- {text_value(item)}" for item in report.get("risk_notes", []))
    errors = report.get("errors", [])
    error_text = "\n".join(f"- {text_value(item)}" for item in errors) if errors else "- 无。"
    return f"""# AStockFastLane 盘后报告

## 1. 报告说明

- 方法：{text_value(meta.get("method"), "rule_based")}
- 生成时间：{text_value(meta.get("created_at"))}
- {DISCLAIMER}
- 不自动写入 watchlist。

## 2. 今日热点主线

{md_table(["强度", "分数", "标题"], mainline_rows)}
## 3. 主线持续性观察

- 结合 hot_events、trend_analysis 与 candidate_review 做规则版整理。
- 重点看热点强度、趋势状态、人工审核状态是否一致。
- 只做观察、跟踪、人工确认与风险记录。

## 4. 重点审核名单

{md_table(["代码", "名称", "分层", "分数", "趋势", "manual_status", "review_note"], selected_rows)}
## 5. 人工审核状态汇总

{md_table(["status", "count"], status_rows)}
## 6. 风向标股票表

{md_table(["股票", "代码", "分层", "趋势", "人工状态", "关注理由"], wind_rows)}
## 7. 明日观察重点

{watch_points}

## 8. 风险提示

{risks}

## 数据健康

{error_text}
"""


def write_outputs(report: dict[str, Any]) -> tuple[Path, Path, Path, Path]:
    stamp = today_stamp()
    dated_json = PROJECT_ROOT / "data" / "analysis" / f"daily_after_close_report_{stamp}.json"
    dated_md = PROJECT_ROOT / "reports" / f"daily_after_close_report_{stamp}.md"
    for path in (DAILY_JSON_LATEST_PATH, dated_json):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = render_markdown(report)
    for path in (DAILY_MD_LATEST_PATH, dated_md):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
    return DAILY_JSON_LATEST_PATH, dated_json, DAILY_MD_LATEST_PATH, dated_md


def main() -> int:
    report = build_report()
    latest_json, dated_json, latest_md, dated_md = write_outputs(report)
    print(f"json: {relative_path(latest_json)}")
    print(f"json dated: {relative_path(dated_json)}")
    print(f"markdown: {relative_path(latest_md)}")
    print(f"markdown dated: {relative_path(dated_md)}")
    print(f"selected_candidates: {len(report.get('selected_candidates', []))}")
    print(f"manual_status_summary: {report.get('manual_status_summary', {})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
