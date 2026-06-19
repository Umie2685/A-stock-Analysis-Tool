from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOT_EVENTS_PATH = PROJECT_ROOT / "data" / "analysis" / "hot_events_latest.json"
WATCHLIST_PATH = PROJECT_ROOT / "config" / "watchlist.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "analysis"
LATEST_JSON_PATH = OUTPUT_DIR / "candidate_watchlist_latest.json"
LATEST_MD_PATH = PROJECT_ROOT / "reports" / "candidate_watchlist_latest.md"
LOCAL_TZ = timezone(timedelta(hours=8))
DISCLAIMER = "候选观察股仅用于热点研究辅助，不构成投资建议、交易建议或交易信号，不承诺任何回报。"
IMPACT_WEIGHT = {"high": 6, "medium": 3, "low": 1, "unknown": 0}
IMPACT_RANK = {"high": 3, "medium": 2, "low": 1, "unknown": 0}


def now_local() -> datetime:
    return datetime.now(LOCAL_TZ)


def relative_path(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def read_json_object(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [f"File not found: {relative_path(path)}"]
    except json.JSONDecodeError as exc:
        return None, [f"JSON decode failed: {relative_path(path)}: {exc}"]
    except OSError as exc:
        return None, [f"Read failed: {relative_path(path)}: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"JSON root is not an object: {relative_path(path)}"]
    return payload, []


def text_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(text_value(item) for item in value)
    if isinstance(value, dict):
        return " ".join(text_value(item) for item in value.values())
    return str(value).strip()


def list_texts(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [text_value(value) for value in values if text_value(value)]


def unique_append(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def as_score(value: Any) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        return 0
    return max(1, min(5, score))


def normalize_strength(value: Any) -> str:
    text = text_value(value).lower()
    return text if text in IMPACT_WEIGHT else "unknown"


def concept_names(event: dict[str, Any]) -> list[str]:
    names: list[str] = []
    concepts = event.get("related_concepts", [])
    if not isinstance(concepts, list):
        return names
    for concept in concepts:
        if isinstance(concept, dict):
            unique_append(names, text_value(concept.get("concept")))
    return names


def enabled_watchlist_codes(payload: dict[str, Any] | None) -> set[str]:
    if not payload:
        return set()
    items = payload.get("items", [])
    if not isinstance(items, list):
        return set()
    codes: set[str] = set()
    for item in items:
        if isinstance(item, dict) and item.get("enabled", True) is True:
            code = text_value(item.get("code"))
            if code:
                codes.add(code)
    return codes


def empty_bucket(stock: dict[str, Any], in_watchlist: bool) -> dict[str, Any]:
    return {
        "code": text_value(stock.get("code")),
        "name": text_value(stock.get("name")),
        "related_concepts": [],
        "source_event_titles": [],
        "source_event_ids": [],
        "event_strengths": [],
        "relevance_scores": [],
        "roles": [],
        "reasons": [],
        "risk_notes": [],
        "in_watchlist": in_watchlist,
        "label": "candidate_watchlist",
    }


def collect_candidates(hot_payload: dict[str, Any] | None, watchlist_codes: set[str]) -> list[dict[str, Any]]:
    events = hot_payload.get("hot_events", []) if hot_payload else []
    if not isinstance(events, list):
        return []

    buckets: dict[str, dict[str, Any]] = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        title = text_value(event.get("title")) or "-"
        event_id = text_value(event.get("event_id")) or title
        strength = normalize_strength(event.get("impact_strength"))
        concepts = concept_names(event)
        stocks = event.get("related_stocks", [])
        if not isinstance(stocks, list):
            continue

        event_seen_codes: set[str] = set()
        for stock in stocks:
            if not isinstance(stock, dict):
                continue
            code = text_value(stock.get("code"))
            if not code:
                continue
            bucket = buckets.setdefault(code, empty_bucket(stock, code in watchlist_codes))
            if not bucket["name"]:
                bucket["name"] = text_value(stock.get("name"))
            for concept in concepts:
                unique_append(bucket["related_concepts"], concept)
            unique_append(bucket["source_event_titles"], title)
            unique_append(bucket["source_event_ids"], event_id)
            unique_append(bucket["roles"], text_value(stock.get("role")))
            unique_append(bucket["reasons"], text_value(stock.get("reason")))
            unique_append(bucket["risk_notes"], text_value(stock.get("risk_note")))
            score = as_score(stock.get("relevance_score"))
            if score:
                bucket["relevance_scores"].append(score)
            if code not in event_seen_codes:
                bucket["event_strengths"].append(strength)
                event_seen_codes.add(code)

    candidates: list[dict[str, Any]] = []
    for bucket in buckets.values():
        scores = bucket.pop("relevance_scores")
        strengths = bucket.pop("event_strengths")
        event_count = len(bucket["source_event_ids"])
        relevance_score_max = max(scores) if scores else 0
        relevance_score_avg = round(mean(scores), 2) if scores else 0
        max_impact_strength = "unknown"
        for strength in strengths:
            if IMPACT_RANK[strength] > IMPACT_RANK[max_impact_strength]:
                max_impact_strength = strength
        heat_score = round(
            sum(IMPACT_WEIGHT[strength] for strength in strengths)
            + event_count * 2
            + relevance_score_max * 1.5
            + relevance_score_avg,
            2,
        )
        bucket.update(
            {
                "heat_score": heat_score,
                "event_count": event_count,
                "max_impact_strength": max_impact_strength,
                "relevance_score_max": relevance_score_max,
                "relevance_score_avg": relevance_score_avg,
            }
        )
        candidates.append(bucket)

    candidates.sort(
        key=lambda item: (
            -float(item.get("heat_score", 0)),
            -int(item.get("event_count", 0)),
            text_value(item.get("code")),
        )
    )
    return candidates


def render_markdown(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        candidates = []

    lines = [
        "# AStockFastLane 候选观察股",
        "",
        "## 1. 报告说明",
        "",
        "仅用于热点研究辅助，不构成投资建议。",
        "",
        f"- 生成时间：{payload.get('generated_at', '-')}",
        f"- 输入热点：{payload.get('source_hot_events', '-')}",
        f"- 输入 watchlist：{payload.get('source_watchlist', '-')}",
        "",
        "## 2. 候选观察股概览",
        "",
        f"- 候选观察股数量：{payload.get('candidate_count', 0)}",
        f"- 已在 watchlist：{payload.get('in_watchlist_count', 0)}",
        f"- 未在 watchlist：{payload.get('not_in_watchlist_count', 0)}",
        "",
        "## 3. 候选观察股列表",
        "",
    ]

    if candidates:
        for index, item in enumerate(candidates, start=1):
            lines.extend(
                [
                    f"### {index}. {item.get('code', '-')} {item.get('name', '-')}",
                    "",
                    f"- 热度评分：{item.get('heat_score', 0)}",
                    f"- 命中概念：{'；'.join(list_texts(item.get('related_concepts'))) or '-'}",
                    f"- 来源热点：{'；'.join(list_texts(item.get('source_event_titles'))) or '-'}",
                    f"- 相关角色：{'；'.join(list_texts(item.get('roles'))) or '-'}",
                    f"- 相关理由：{'；'.join(list_texts(item.get('reasons'))) or '-'}",
                    f"- 风险提示：{'；'.join(list_texts(item.get('risk_notes'))) or '-'}",
                    f"- 是否已在 watchlist：{item.get('in_watchlist')}",
                    "",
                ]
            )
    else:
        lines.append("暂无候选观察股。")

    warnings = payload.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        lines.extend(["", "## 数据健康提示", ""])
        for warning in warnings:
            lines.append(f"- warning: {warning}")

    lines.extend(["", "## 4. 免责声明", "", DISCLAIMER, ""])
    return "\n".join(lines)


def build_candidate_watchlist() -> dict[str, Any]:
    warnings: list[str] = []
    hot_payload, hot_errors = read_json_object(HOT_EVENTS_PATH)
    watchlist_payload, watchlist_errors = read_json_object(WATCHLIST_PATH)
    warnings.extend(hot_errors)
    warnings.extend(watchlist_errors)

    watchlist_codes = enabled_watchlist_codes(watchlist_payload)
    candidates = collect_candidates(hot_payload, watchlist_codes)
    in_count = sum(1 for item in candidates if item.get("in_watchlist") is True)

    return {
        "schema_version": 1,
        "analysis_name": "candidate_watchlist",
        "generated_at": now_local().isoformat(),
        "source_hot_events": relative_path(HOT_EVENTS_PATH),
        "source_watchlist": relative_path(WATCHLIST_PATH),
        "candidate_count": len(candidates),
        "in_watchlist_count": in_count,
        "not_in_watchlist_count": len(candidates) - in_count,
        "sort_rule": "heat_score_desc",
        "score_rule": "event strength weight + event count + relevance score",
        "candidates": candidates,
        "warnings": warnings,
        "disclaimer": DISCLAIMER,
    }


def write_outputs(payload: dict[str, Any]) -> tuple[Path, Path, Path, Path]:
    today = now_local().strftime("%Y%m%d")
    dated_json_path = OUTPUT_DIR / f"candidate_watchlist_{today}.json"
    dated_md_path = PROJECT_ROOT / "reports" / f"candidate_watchlist_{today}.md"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    md_text = render_markdown(payload)

    LATEST_JSON_PATH.write_text(json_text, encoding="utf-8")
    dated_json_path.write_text(json_text, encoding="utf-8")
    LATEST_MD_PATH.write_text(md_text, encoding="utf-8")
    dated_md_path.write_text(md_text, encoding="utf-8")
    return LATEST_JSON_PATH, dated_json_path, LATEST_MD_PATH, dated_md_path


def main() -> int:
    payload = build_candidate_watchlist()
    json_path, dated_json_path, md_path, dated_md_path = write_outputs(payload)
    print("Candidate watchlist analysis: candidate_watchlist")
    print(f"Candidate count: {payload.get('candidate_count')}")
    print(f"In watchlist: {payload.get('in_watchlist_count')}")
    print(f"Not in watchlist: {payload.get('not_in_watchlist_count')}")
    print(f"Latest JSON: {relative_path(json_path)}")
    print(f"Dated JSON: {relative_path(dated_json_path)}")
    print(f"Latest Markdown: {relative_path(md_path)}")
    print(f"Dated Markdown: {relative_path(dated_md_path)}")
    warnings = payload.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
