from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_PATH = PROJECT_ROOT / "data" / "evidence" / "fast_evidence_pack_latest.json"
MANUAL_HOT_EVENTS_PATH = PROJECT_ROOT / "data" / "manual" / "hot_events_manual.json"
CONCEPT_MAP_PATH = PROJECT_ROOT / "config" / "concept_map.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "analysis"
LATEST_JSON_PATH = OUTPUT_DIR / "hot_events_latest.json"
LATEST_MD_PATH = PROJECT_ROOT / "reports" / "hot_events_latest.md"
LOCAL_TZ = timezone(timedelta(hours=8))

ANALYSIS_LEVEL = "rule_based"
DISCLAIMER = "规则版热点分析仅用于公开信息整理和研究辅助，不构成投资建议、交易建议或交易信号，不承诺任何回报。"
STRONG_TRIGGER_WORDS = [
    "政策",
    "涨价",
    "订单",
    "制裁",
    "出口管制",
    "禁令",
    "突破",
    "量产",
    "并购",
    "回购",
    "中标",
    "签约",
    "投产",
    "扩产",
    "核准",
    "发射成功",
    "新品发布",
]
NEGATIVE_TRIGGER_WORDS = [
    "制裁",
    "出口管制",
    "禁令",
    "调查",
    "处罚",
    "延期",
    "下滑",
    "风险",
    "事故",
    "价格回落",
]
POSITIVE_TRIGGER_WORDS = [
    "政策",
    "涨价",
    "订单",
    "突破",
    "量产",
    "中标",
    "签约",
    "投产",
    "扩产",
    "核准",
    "发射成功",
    "新品发布",
]
IMPACT_RANK = {"high": 0, "medium": 1, "low": 2, "unknown": 3}


def now_local() -> datetime:
    return datetime.now(LOCAL_TZ)


def relative_path(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def read_json_object(path: Path, *, missing_is_warning: bool = False) -> tuple[dict[str, Any] | None, list[str], list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        message = f"File not found: {relative_path(path)}"
        return None, ([message] if missing_is_warning else []), ([] if missing_is_warning else [message])
    except json.JSONDecodeError as exc:
        return None, [], [f"JSON decode failed: {relative_path(path)}: {exc}"]
    except OSError as exc:
        return None, [], [f"Read failed: {relative_path(path)}: {exc}"]

    if not isinstance(payload, dict):
        return None, [], [f"JSON root is not an object: {relative_path(path)}"]
    return payload, [], []


def text_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(text_value(item) for item in value)
    if isinstance(value, dict):
        return " ".join(text_value(item) for item in value.values())
    return str(value).strip()


def list_value(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text_value(item) for item in value if text_value(item)]


def first_text(item: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        text = text_value(item.get(key))
        if text:
            return text
    return ""


def raw_ref(item: dict[str, Any]) -> dict[str, Any]:
    value = item.get("raw_ref")
    return value if isinstance(value, dict) else {}


def raw_payload(item: dict[str, Any]) -> dict[str, Any]:
    value = raw_ref(item).get("raw")
    return value if isinstance(value, dict) else {}


def source_type(item: dict[str, Any]) -> str:
    value = text_value(item.get("input_source"))
    if value:
        return value
    for key in ("evidence_type", "category", "source"):
        raw = text_value(item.get(key)).lower().replace("-", "_")
        if raw in {"news", "eastmoney_news"}:
            return "evidence_news"
        if raw == "manual_hot_event":
            return "manual_hot_event"
    return "unknown"


def event_type(item: dict[str, Any]) -> str:
    input_source = source_type(item)
    if input_source == "manual_hot_event":
        return "manual_hot_event"
    return "news" if input_source == "evidence_news" else "unknown"


def evidence_items(pack: dict[str, Any], warnings: list[str]) -> list[dict[str, Any]]:
    items = pack.get("evidence_items", [])
    if not isinstance(items, list):
        warnings.append("fast_evidence_pack_latest.json evidence_items is not a list")
        return []
    return [item for item in items if isinstance(item, dict)]


def manual_items(payload: dict[str, Any] | None, warnings: list[str]) -> list[dict[str, Any]]:
    if not payload:
        return []
    items = payload.get("items", [])
    if not isinstance(items, list):
        warnings.append("hot_events_manual.json items is not a list")
        return []
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            warnings.append(f"hot_events_manual.json items[{index}] is not an object")
            continue
        if item.get("enabled", True) is not True:
            continue
        normalized.append(
            {
                "evidence_id": f"manual_hot_event_{index:03d}",
                "evidence_type": "manual_hot_event",
                "input_source": "manual_hot_event",
                "title": text_value(item.get("title")),
                "summary": text_value(item.get("summary")),
                "source": "manual_hot_event",
                "publish_time": text_value(item.get("publish_time")),
                "url": text_value(item.get("url")),
                "note": text_value(item.get("note")),
            }
        )
    return normalized


def evidence_news_items(pack: dict[str, Any] | None, warnings: list[str]) -> list[dict[str, Any]]:
    if not pack:
        return []
    news: list[dict[str, Any]] = []
    for item in evidence_items(pack, warnings):
        kind = text_value(item.get("evidence_type") or item.get("category") or item.get("source")).lower().replace("-", "_")
        if kind in {"news", "eastmoney_news"}:
            copied = dict(item)
            copied["input_source"] = "evidence_news"
            news.append(copied)
    return news


def as_score(value: Any) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        return 0
    return max(1, min(5, score))


def load_concepts(payload: dict[str, Any] | None, warnings: list[str]) -> list[dict[str, Any]]:
    if not payload:
        return []
    concepts = payload.get("concepts", [])
    if not isinstance(concepts, list):
        warnings.append("concept_map.json concepts is not a list")
        return []

    valid: list[dict[str, Any]] = []
    for index, concept in enumerate(concepts, start=1):
        if not isinstance(concept, dict):
            warnings.append(f"concepts[{index}] is not an object")
            continue
        name = text_value(concept.get("concept"))
        if not name:
            warnings.append(f"concepts[{index}].concept is empty")
            continue
        raw_stocks = concept.get("related_stocks", [])
        stocks = raw_stocks if isinstance(raw_stocks, list) else []
        valid.append(
            {
                "concept": name,
                "keywords": list_value(concept.get("keywords")),
                "impact_logic": text_value(concept.get("impact_logic")),
                "typical_positive_triggers": list_value(concept.get("typical_positive_triggers")),
                "typical_negative_triggers": list_value(concept.get("typical_negative_triggers")),
                "risk_notes": list_value(concept.get("risk_notes")),
                "related_stocks": [stock for stock in stocks if isinstance(stock, dict)],
            }
        )
    return valid


def stock_identity(item: dict[str, Any]) -> dict[str, str]:
    raw = raw_payload(item)
    code = (
        first_text(item, ["query_code", "stock_code", "symbol", "code"])
        or first_text(raw_ref(item), ["query_code", "stock_code", "symbol", "code"])
        or first_text(raw, ["stockCode", "secCode", "code"])
    )
    name = (
        first_text(item, ["query_name", "stock_name", "company", "name"])
        or first_text(raw_ref(item), ["query_name", "stock_name", "company", "name"])
        or first_text(raw, ["stockName", "secName", "name"])
    )
    market = first_text(item, ["query_market", "market"]) or first_text(raw_ref(item), ["query_market", "market"])
    return {"code": code, "name": name, "market": market}


def searchable_text(item: dict[str, Any]) -> str:
    raw = raw_payload(item)
    fields = [
        item.get("title"),
        item.get("summary"),
        item.get("note"),
        item.get("tags"),
        item.get("related_symbols"),
        raw_ref(item).get("title"),
        raw_ref(item).get("summary"),
        raw.get("title"),
        raw.get("summary"),
        raw.get("stockList"),
    ]
    stock = stock_identity(item)
    fields.extend([stock["code"], stock["name"], stock["market"]])
    return " ".join(text_value(field) for field in fields if text_value(field)).lower()


def matched_terms(haystack: str, terms: list[str]) -> list[str]:
    return [term for term in terms if term and term.lower() in haystack]


def normalize_related_stock(related: dict[str, Any]) -> dict[str, Any]:
    return {
        "code": text_value(related.get("code")),
        "name": text_value(related.get("name")),
        "role": text_value(related.get("role")) or "候选观察股",
        "relevance_score": as_score(related.get("relevance_score")),
        "reason": text_value(related.get("reason")),
        "risk_note": text_value(related.get("risk_note")),
        "link_type": "candidate_watchlist",
    }


def match_concept(item: dict[str, Any], concept: dict[str, Any]) -> dict[str, Any] | None:
    haystack = searchable_text(item)
    matched_keywords = matched_terms(haystack, concept["keywords"])
    stock = stock_identity(item)
    matched_stock_links: list[dict[str, Any]] = []

    for related in concept["related_stocks"]:
        normalized = normalize_related_stock(related)
        code = normalized["code"]
        name = normalized["name"]
        if matched_keywords or (code and code == stock["code"]) or (name and name.lower() in haystack):
            matched_stock_links.append(normalized)

    if not matched_keywords and not matched_stock_links:
        return None

    reasons = []
    if matched_keywords:
        reasons.append("keyword")
    if matched_stock_links:
        reasons.append("candidate_watchlist")

    return {
        "concept": concept["concept"],
        "match_reasons": reasons,
        "matched_keywords": matched_keywords,
        "impact_logic": concept["impact_logic"],
        "positive_triggers": concept["typical_positive_triggers"],
        "negative_triggers": concept["typical_negative_triggers"],
        "risk_notes": concept["risk_notes"],
        "related_stocks": matched_stock_links,
    }


def unique_texts(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def flatten_related_stocks(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    stocks: list[dict[str, Any]] = []
    for match in matches:
        for stock in match.get("related_stocks", []):
            key = (text_value(stock.get("code")), text_value(stock.get("name")))
            if key in seen:
                continue
            seen.add(key)
            stocks.append(stock)
    return stocks


def classify_strength(matches: list[dict[str, Any]], title_triggers: list[str]) -> tuple[str, int]:
    concept_count = len(matches)
    keyword_count = sum(len(match.get("matched_keywords", [])) for match in matches)
    score = concept_count * 2 + keyword_count + len(title_triggers) * 2
    if concept_count >= 2 or score >= 7:
        return "high", score
    if concept_count >= 1 or score >= 3:
        return "medium", score
    return "low", score


def classify_direction(positive_triggers: list[str], negative_triggers: list[str], matches: list[dict[str, Any]]) -> str:
    if negative_triggers and not positive_triggers:
        return "risk_alert"
    if positive_triggers and not negative_triggers:
        return "attention_catalyst"
    if matches:
        return "concept_related"
    return "unclassified"


def reason_for_event(matches: list[dict[str, Any]], title_triggers: list[str], impact_strength: str) -> str:
    if not matches:
        if title_triggers:
            return f"未命中概念映射，但标题包含强触发词：{', '.join(title_triggers)}；按低强度保留为热点事件。"
        return "未命中概念映射；按规则保留为热点事件，供后续人工筛选。"
    parts = []
    for match in matches:
        keywords = match.get("matched_keywords", [])
        stock_count = len(match.get("related_stocks", []))
        detail = f"{match.get('concept', '-')}"
        if keywords:
            detail += f" 命中关键词：{', '.join(keywords)}"
        if stock_count:
            detail += f"；包含 {stock_count} 个候选观察股线索"
        parts.append(detail)
    trigger_text = f"；标题强触发词：{', '.join(title_triggers)}" if title_triggers else ""
    return f"规则归类为 {impact_strength}：{' | '.join(parts)}{trigger_text}。"


def concept_summary(matches: list[dict[str, Any]], key: str) -> list[str]:
    values: list[str] = []
    for match in matches:
        raw_values = match.get(key, [])
        if isinstance(raw_values, list):
            values.extend(text_value(value) for value in raw_values)
    return unique_texts(values)


def build_event(item: dict[str, Any], index: int, concepts: list[dict[str, Any]]) -> dict[str, Any]:
    title = first_text(item, ["title"]) or first_text(raw_ref(item), ["title"])
    publish_time = first_text(item, ["publish_time", "date"]) or first_text(raw_ref(item), ["publish_time", "date"])
    url = first_text(item, ["url"]) or first_text(raw_ref(item), ["url"])
    haystack = searchable_text(item)
    matches = [match for concept in concepts if (match := match_concept(item, concept))]
    title_triggers = matched_terms(title.lower(), STRONG_TRIGGER_WORDS)
    raw_positive = matched_terms(haystack, POSITIVE_TRIGGER_WORDS)
    raw_negative = matched_terms(haystack, NEGATIVE_TRIGGER_WORDS)
    positive_triggers = unique_texts(raw_positive + concept_summary(matches, "positive_triggers"))
    negative_triggers = unique_texts(raw_negative + concept_summary(matches, "negative_triggers"))
    impact_strength, impact_score = classify_strength(matches, title_triggers)
    impact_logic = unique_texts([text_value(match.get("impact_logic")) for match in matches])
    risk_notes = unique_texts(concept_summary(matches, "risk_notes"))
    related_stocks = flatten_related_stocks(matches)

    return {
        "event_id": f"hot_event_{index:03d}",
        "evidence_id": first_text(item, ["evidence_id"]) or f"evidence_{index:03d}",
        "evidence_type": event_type(item),
        "input_source": source_type(item),
        "title": title,
        "summary": first_text(item, ["summary"]) or first_text(raw_ref(item), ["summary"]),
        "publish_time": publish_time,
        "source": first_text(item, ["source"]) or source_type(item),
        "url": url,
        "stock": stock_identity(item),
        "impact_direction": classify_direction(raw_positive, raw_negative, matches),
        "impact_strength": impact_strength,
        "impact_score": impact_score,
        "impact_logic": impact_logic,
        "risk_notes": risk_notes,
        "positive_triggers": positive_triggers,
        "negative_triggers": negative_triggers,
        "strong_trigger_words": title_triggers,
        "related_concepts": matches,
        "related_stocks": related_stocks,
        "reason": reason_for_event(matches, title_triggers, impact_strength),
        "analysis_level": ANALYSIS_LEVEL,
        "classification_method": "offline_rule_keyword_trigger_candidate_watchlist_match",
        "confidence_note": "规则分析结果仅用于研究辅助和线索归档，不代表投资建议。",
    }


def build_hot_events() -> tuple[dict[str, Any], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    pack, pack_warnings, pack_errors = read_json_object(EVIDENCE_PATH)
    manual_payload, manual_warnings, manual_errors = read_json_object(MANUAL_HOT_EVENTS_PATH, missing_is_warning=True)
    concept_map, concept_warnings, concept_errors = read_json_object(CONCEPT_MAP_PATH)
    warnings.extend(pack_warnings + manual_warnings + concept_warnings)
    errors.extend(pack_errors + manual_errors + concept_errors)

    concepts = load_concepts(concept_map, warnings)
    source_items = evidence_news_items(pack, warnings) + manual_items(manual_payload, warnings)
    events = [build_event(item, index, concepts) for index, item in enumerate(source_items, start=1)]
    events.sort(
        key=lambda event: (
            IMPACT_RANK.get(text_value(event.get("impact_strength")), 99),
            -int(event.get("impact_score", 0)),
            text_value(event.get("publish_time")),
        )
    )
    for index, event in enumerate(events, start=1):
        event["event_id"] = f"hot_event_{index:03d}"

    concept_counter: Counter[str] = Counter()
    input_counter: Counter[str] = Counter()
    for event in events:
        input_counter[text_value(event.get("input_source")) or "unknown"] += 1
        for match in event.get("related_concepts", []):
            concept_counter[text_value(match.get("concept"))] += 1

    related_stock_examples: list[dict[str, Any]] = []
    seen_stock_keys: set[tuple[str, str]] = set()
    for event in events:
        for stock in event.get("related_stocks", []):
            key = (text_value(stock.get("code")), text_value(stock.get("name")))
            if key not in seen_stock_keys:
                seen_stock_keys.add(key)
                related_stock_examples.append(stock)

    generated_at = now_local()
    payload = {
        "schema_version": 3,
        "analysis_name": "hot_events",
        "analysis_level": ANALYSIS_LEVEL,
        "generated_at": generated_at.isoformat(),
        "source_evidence_pack": relative_path(EVIDENCE_PATH),
        "manual_hot_events": relative_path(MANUAL_HOT_EVENTS_PATH),
        "concept_map": relative_path(CONCEPT_MAP_PATH),
        "success": not errors,
        "event_scope": "evidence_news_plus_manual_hot_event",
        "input_source_counts": dict(input_counter),
        "event_count": len(events),
        "matched_concepts": [{"concept": name, "event_count": count} for name, count in concept_counter.most_common()],
        "candidate_watchlist_count": len(related_stock_examples),
        "related_stock_examples": related_stock_examples[:20],
        "hot_events": events,
        "warnings": warnings,
        "errors": errors,
        "disclaimer": DISCLAIMER,
    }
    return payload, warnings, errors


def md_join(values: Any, fallback: str = "-") -> str:
    if not isinstance(values, list):
        value = text_value(values)
        return value if value else fallback
    texts = [text_value(value) for value in values if text_value(value) and text_value(value) != "-"]
    return "；".join(texts) if texts else fallback


def concept_names(event: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for concept in event.get("related_concepts", []):
        if isinstance(concept, dict):
            name = text_value(concept.get("concept"))
            if name:
                names.append(name)
    return names


def event_keywords(event: dict[str, Any]) -> list[str]:
    values = list_value(event.get("strong_trigger_words"))
    for concept in event.get("related_concepts", []):
        if isinstance(concept, dict):
            values.extend(list_value(concept.get("matched_keywords")))
    return unique_texts(values)


def stock_lines(stocks: Any) -> tuple[str, str, str]:
    if not isinstance(stocks, list) or not stocks:
        return "-", "-", "-"
    names: list[str] = []
    scores: list[str] = []
    risks: list[str] = []
    for stock in stocks:
        if not isinstance(stock, dict):
            continue
        label = f"{text_value(stock.get('code'))} {text_value(stock.get('name'))}".strip()
        role = text_value(stock.get("role"))
        names.append(f"{label}（{role}）" if role else label)
        score = text_value(stock.get("relevance_score"))
        if score:
            scores.append(f"{label or '候选观察股'}：{score}/5")
        risk = text_value(stock.get("risk_note"))
        if risk:
            risks.append(f"{label or '候选观察股'}：{risk}")
    return md_join(names), md_join(scores), md_join(risks)


def render_markdown(payload: dict[str, Any]) -> str:
    matched_concepts = payload.get("matched_concepts", [])
    concept_text = "-"
    if isinstance(matched_concepts, list) and matched_concepts:
        concept_text = "；".join(
            f"{item.get('concept', '-')}({item.get('event_count', 0)})"
            for item in matched_concepts
            if isinstance(item, dict)
        )

    lines = [
        "# AStockFastLane 热点事件分析",
        "",
        "## 1. 报告说明",
        "",
        "说明：规则版热点分析，仅用于研究辅助，不构成投资建议。",
        "",
        f"- 分析方式：{payload.get('analysis_level', ANALYSIS_LEVEL)}",
        f"- 生成时间：{payload.get('generated_at', '-')}",
        f"- 输入 Evidence Pack：{payload.get('source_evidence_pack', '-')}",
        f"- 手动热点输入：{payload.get('manual_hot_events', '-')}",
        f"- 概念映射：{payload.get('concept_map', '-')}",
        "",
        "## 2. 热点概览",
        "",
        f"- 事件数量：{payload.get('event_count', 0)}",
        f"- 输入来源：{payload.get('input_source_counts', {})}",
        f"- 命中概念：{concept_text}",
        f"- 候选观察股数量：{payload.get('candidate_watchlist_count', 0)}",
        "",
        "## 3. 热点事件列表",
        "",
    ]

    events = payload.get("hot_events", [])
    if isinstance(events, list) and events:
        for index, event in enumerate(events, start=1):
            if not isinstance(event, dict):
                continue
            candidate_stocks, relevance_scores, stock_risks = stock_lines(event.get("related_stocks", []))
            event_risks = md_join(event.get("risk_notes", []))
            risk_text = md_join([event_risks, stock_risks], "-")
            lines.extend(
                [
                    f"### {index}. {event.get('title', '-')}",
                    "",
                    f"- 输入来源：{event.get('input_source', '-')}",
                    f"- 事件类型：{event.get('evidence_type', '-')}",
                    f"- 影响方向：{event.get('impact_direction', '-')}",
                    f"- 影响力度：{event.get('impact_strength', '-')}",
                    f"- 相关概念：{md_join(concept_names(event))}",
                    f"- 传导逻辑：{md_join(event.get('impact_logic', []))}",
                    f"- 候选观察股：{candidate_stocks}",
                    f"- 相关度：{relevance_scores}",
                    f"- 风险提示：{risk_text}",
                    f"- 正向触发项：{md_join(event.get('positive_triggers', []))}",
                    f"- 负向触发项：{md_join(event.get('negative_triggers', []))}",
                    f"- 规则命中关键词：{md_join(event_keywords(event))}",
                    f"- 规则判断理由：{event.get('reason', '-')}",
                    f"- 分析方式：{event.get('analysis_level', ANALYSIS_LEVEL)}",
                    f"- URL：{event.get('url', '-')}",
                    "",
                ]
            )
    else:
        lines.append("暂无热点事件。")

    if payload.get("warnings"):
        lines.extend(["", "## 数据健康提示", ""])
        for warning in payload.get("warnings", []):
            lines.append(f"- warning: {warning}")
    if payload.get("errors"):
        lines.extend(["", "## 错误提示", ""])
        for error in payload.get("errors", []):
            lines.append(f"- error: {error}")

    lines.extend(["", "## 4. 免责声明", "", DISCLAIMER, ""])
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any]) -> tuple[Path, Path, Path, Path]:
    generated_at = now_local()
    today = generated_at.strftime("%Y%m%d")
    dated_json_path = OUTPUT_DIR / f"hot_events_{today}.json"
    dated_md_path = PROJECT_ROOT / "reports" / f"hot_events_{today}.md"

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
    payload, warnings, errors = build_hot_events()
    json_path, dated_json_path, md_path, dated_md_path = write_outputs(payload)

    concepts = [item["concept"] for item in payload.get("matched_concepts", []) if isinstance(item, dict)]
    strengths = [event.get("impact_strength") for event in payload.get("hot_events", []) if isinstance(event, dict)]
    print("Hot event analysis: hot_events")
    print(f"Success: {payload.get('success')}")
    print(f"Analysis level: {payload.get('analysis_level')}")
    print(f"Event scope: {payload.get('event_scope')}")
    print(f"Input sources: {payload.get('input_source_counts')}")
    print(f"Event count: {payload.get('event_count')}")
    print(f"Matched concepts: {', '.join(concepts) if concepts else '-'}")
    print(f"Candidate watchlist count: {payload.get('candidate_watchlist_count')}")
    print(f"Impact strength order: {', '.join(text_value(item) for item in strengths[:12]) if strengths else '-'}")
    print(f"Latest JSON: {relative_path(json_path)}")
    print(f"Dated JSON: {relative_path(dated_json_path)}")
    print(f"Latest Markdown: {relative_path(md_path)}")
    print(f"Dated Markdown: {relative_path(dated_md_path)}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"- {error}")
    return 0 if payload.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
