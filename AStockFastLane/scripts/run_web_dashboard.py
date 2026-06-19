from __future__ import annotations

import argparse
from datetime import datetime
import html
import json
import re
from collections import Counter, OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WATCHLIST_PATH = PROJECT_ROOT / "config" / "watchlist.json"
EVIDENCE_PATH = PROJECT_ROOT / "data" / "evidence" / "fast_evidence_pack_latest.json"
HOT_EVENTS_JSON_PATH = PROJECT_ROOT / "data" / "analysis" / "hot_events_latest.json"
HOT_EVENTS_MD_PATH = PROJECT_ROOT / "reports" / "hot_events_latest.md"
CANDIDATE_WATCHLIST_JSON_PATH = PROJECT_ROOT / "data" / "analysis" / "candidate_watchlist_latest.json"
CANDIDATE_WATCHLIST_MD_PATH = PROJECT_ROOT / "reports" / "candidate_watchlist_latest.md"
CANDIDATE_REVIEW_JSON_PATH = PROJECT_ROOT / "data" / "analysis" / "candidate_review_latest.json"
CANDIDATE_REVIEW_MD_PATH = PROJECT_ROOT / "reports" / "candidate_review_latest.md"
CANDIDATE_REVIEW_STATUS_PATH = PROJECT_ROOT / "data" / "manual" / "candidate_review_status.json"
TREND_ANALYSIS_JSON_PATH = PROJECT_ROOT / "data" / "analysis" / "trend_analysis_latest.json"
TREND_ANALYSIS_MD_PATH = PROJECT_ROOT / "reports" / "trend_analysis_latest.md"
DAILY_K_PATH = PROJECT_ROOT / "data" / "market" / "daily_k_latest.json"
WEEKLY_K_PATH = PROJECT_ROOT / "data" / "market" / "weekly_k_latest.json"
DAILY_AFTER_CLOSE_JSON_PATH = PROJECT_ROOT / "data" / "analysis" / "daily_after_close_report_latest.json"
DAILY_AFTER_CLOSE_MD_PATH = PROJECT_ROOT / "reports" / "daily_after_close_report_latest.md"
FAST_REPORT_PATH = PROJECT_ROOT / "reports" / "fast_report_latest.md"
HEALTH_CHECK_PATHS = [
    HOT_EVENTS_JSON_PATH,
    HOT_EVENTS_MD_PATH,
    CANDIDATE_WATCHLIST_JSON_PATH,
    CANDIDATE_WATCHLIST_MD_PATH,
    CANDIDATE_REVIEW_JSON_PATH,
    CANDIDATE_REVIEW_MD_PATH,
    CANDIDATE_REVIEW_STATUS_PATH,
    TREND_ANALYSIS_JSON_PATH,
    TREND_ANALYSIS_MD_PATH,
    DAILY_K_PATH,
    DAILY_AFTER_CLOSE_JSON_PATH,
    DAILY_AFTER_CLOSE_MD_PATH,
    EVIDENCE_PATH,
    FAST_REPORT_PATH,
]
STRENGTH_ORDER = ["high", "medium", "low", "unknown"]
TREND_STATE_ORDER = ["strong_uptrend", "recovering", "sideways", "weakening", "overheated", "unknown"]
TREND_STATE_LABELS = {
    "strong_uptrend": "强势",
    "recovering": "修复",
    "sideways": "震荡",
    "weakening": "走弱",
    "overheated": "过热",
    "unknown": "数据不足",
}
REVIEW_BUCKET_ORDER = ["core_watch", "elastic_watch", "market_height_watch", "trend_watch", "skip", "blocked", "unknown"]
REVIEW_BUCKET_LABELS = {
    "core_watch": "核心观察",
    "elastic_watch": "弹性观察",
    "trend_watch": "趋势观察",
    "market_height_watch": "市场高度观察",
    "skip": "暂不纳入",
    "blocked": "明确排除",
    "unknown": "信息不足",
}
DISCLAIMER = "仅用于公开信息整理和研究辅助，不构成投资建议、交易建议或交易信号，不承诺任何回报。"


def relative_path(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, f"missing: {relative_path(path)}"
    except json.JSONDecodeError as exc:
        return None, f"json decode failed: {relative_path(path)}: {exc}"
    except OSError as exc:
        return None, f"read failed: {relative_path(path)}: {exc}"
    if not isinstance(payload, dict):
        return None, f"json root is not an object: {relative_path(path)}"
    return payload, None


def read_text(path: Path, limit: int | None = None) -> tuple[str, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "", f"missing: {relative_path(path)}"
    except OSError as exc:
        return "", f"read failed: {relative_path(path)}: {exc}"
    return (text[:limit] if limit else text), None


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def format_datetime(value: Any, fallback: str = "-") -> str:
    text = text_value(value)
    if not text or text == "-":
        return fallback
    normalized = text.replace("Z", "+00:00")
    try:
        if len(normalized) == 10 and normalized[4] == "-" and normalized[7] == "-":
            return normalized
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return text
    return parsed.strftime("%Y-%m-%d %H:%M")


ISO_DATETIME_RE = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?")


def format_embedded_datetimes(value: Any) -> str:
    text = text_value(value)
    return ISO_DATETIME_RE.sub(lambda match: format_datetime(match.group(0)), text)


def normalize_legacy_candidate_terms(value: Any) -> str:
    text = "" if value is None else str(value)
    replacements = {
        "候选观察股": "热点候选池",
        "候选观察公司": "热点候选池关联公司",
        "已在 watchlist": "生成时已命中长期 watchlist",
        "未在 watchlist": "生成时未命中长期 watchlist",
        "in_watchlist": "生成时 watchlist 标记",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def ui_text(value: Any) -> str:
    return format_embedded_datetimes(normalize_legacy_candidate_terms(value))


def text_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(text_value(item) for item in value)
    if isinstance(value, dict):
        return " ".join(text_value(item) for item in value.values())
    return str(value).strip()


def join_values(values: Any, sep: str = "；", fallback: str = "-") -> str:
    if not isinstance(values, list):
        value = text_value(values)
        return value if value else fallback
    texts = [text_value(item) for item in values if text_value(item) and text_value(item) != "-"]
    return sep.join(texts) if texts else fallback


def first_text(item: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = text_value(item.get(key))
        if value:
            return value
    return ""


def item_type(item: dict[str, Any]) -> str:
    for key in ("evidence_type", "category", "source"):
        value = text_value(item.get(key)).lower().replace("-", "_")
        if value in {"news", "announcement", "research_report"}:
            return value
        if value == "eastmoney_news":
            return "news"
        if value == "cninfo_announcement":
            return "announcement"
        if value == "eastmoney_report":
            return "research_report"
    return "unknown"


def raw_ref(item: dict[str, Any]) -> dict[str, Any]:
    value = item.get("raw_ref")
    return value if isinstance(value, dict) else {}


def raw_payload(item: dict[str, Any]) -> dict[str, Any]:
    value = raw_ref(item).get("raw")
    return value if isinstance(value, dict) else {}


def evidence_items(pack: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not pack:
        return []
    items = pack.get("evidence_items", [])
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def split_evidence(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    news: list[dict[str, Any]] = []
    announcements: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    for item in items:
        kind = item_type(item)
        if kind == "news":
            news.append(item)
        elif kind == "announcement":
            announcements.append(item)
        elif kind == "research_report":
            reports.append(item)
    return news, announcements, reports


def enabled_watchlist_items(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not payload:
        return []
    items = payload.get("items", [])
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict) and item.get("enabled", True) is True]


def stock_identity(item: dict[str, Any]) -> tuple[str, str, str]:
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
    return code or "-", name or "-", market or "-"


def group_stock_evidence(
    announcements: list[dict[str, Any]], reports: list[dict[str, Any]]
) -> "OrderedDict[tuple[str, str, str], dict[str, list[dict[str, Any]]]]":
    grouped: "OrderedDict[tuple[str, str, str], dict[str, list[dict[str, Any]]]]" = OrderedDict()
    for bucket_name, bucket_items in (("announcements", announcements), ("reports", reports)):
        for item in bucket_items:
            key = stock_identity(item)
            grouped.setdefault(key, {"announcements": [], "reports": []})
            grouped[key][bucket_name].append(item)
    return grouped


def hot_events(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not payload:
        return []
    events = payload.get("hot_events", [])
    return [event for event in events if isinstance(event, dict)] if isinstance(events, list) else []


def candidate_items(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not payload:
        return []
    candidates = payload.get("candidates", [])
    return [item for item in candidates if isinstance(item, dict)] if isinstance(candidates, list) else []


def candidate_review_items(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not payload:
        return []
    items = payload.get("items", [])
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def candidate_review_meta(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}
    meta = payload.get("meta", {})
    return meta if isinstance(meta, dict) else {}


def candidate_review_buckets(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}
    buckets = payload.get("buckets", {})
    return buckets if isinstance(buckets, dict) else {}


def candidate_review_status_items(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not payload:
        return []
    items = payload.get("items", [])
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def build_review_status_index(payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    status_index: dict[str, dict[str, Any]] = {}
    for item in candidate_review_status_items(payload):
        code = text_value(item.get("code"))
        if not code:
            continue
        current = status_index.get(code)
        current_updated_at = text_value(current.get("updated_at")) if current else ""
        item_updated_at = text_value(item.get("updated_at"))
        if current is None or item_updated_at >= current_updated_at:
            status_index[code] = item
    return status_index


def selected_review_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in items if item.get("selected_for_review") is True]


def normalize_strength(value: Any) -> str:
    text = text_value(value).lower()
    return text if text in STRENGTH_ORDER else "unknown"


def group_events_by_strength(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped = {strength: [] for strength in STRENGTH_ORDER}
    for event in events:
        grouped[normalize_strength(event.get("impact_strength"))].append(event)
    return grouped


def strength_counts(events: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter({strength: 0 for strength in STRENGTH_ORDER})
    for event in events:
        counter[normalize_strength(event.get("impact_strength"))] += 1
    return counter


def concept_names(event: dict[str, Any]) -> list[str]:
    related = event.get("related_concepts", [])
    if not isinstance(related, list):
        return []
    return [text_value(item.get("concept")) for item in related if isinstance(item, dict) and text_value(item.get("concept"))]


def matched_keywords(event: dict[str, Any]) -> list[str]:
    keywords: list[str] = []
    for concept in event.get("related_concepts", []):
        if isinstance(concept, dict) and isinstance(concept.get("matched_keywords"), list):
            keywords.extend(text_value(item) for item in concept["matched_keywords"] if text_value(item))
    if isinstance(event.get("strong_trigger_words"), list):
        keywords.extend(text_value(item) for item in event["strong_trigger_words"] if text_value(item))
    seen: set[str] = set()
    result: list[str] = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            result.append(keyword)
    return result


def candidate_stock_rows(event: dict[str, Any]) -> list[str]:
    stocks = event.get("related_stocks", [])
    if not isinstance(stocks, list):
        return []
    rows: list[str] = []
    for stock in stocks:
        if not isinstance(stock, dict):
            continue
        code = text_value(stock.get("code")) or "-"
        name = text_value(stock.get("name")) or "-"
        role = text_value(stock.get("role")) or "-"
        score = text_value(stock.get("relevance_score")) or "-"
        reason = text_value(stock.get("reason")) or "-"
        risk_note = text_value(stock.get("risk_note")) or "-"
        rows.append(
            f"{esc(code)} / {esc(name)} / {esc(ui_text(role))} / relevance_score {esc(score)} / "
            f"reason: {esc(ui_text(reason))} / risk_note: {esc(ui_text(risk_note))}"
        )
    return rows


def render_stats(news_count: int, announcement_count: int, report_count: int) -> str:
    total = news_count + announcement_count + report_count
    stats = [
        ("news", news_count),
        ("announcement", announcement_count),
        ("research_report", report_count),
        ("total", total),
    ]
    return '<section class="grid">' + "".join(
        f'<div class="panel"><div class="label">{esc(label)}</div><div class="stat">{count}</div></div>'
        for label, count in stats
    ) + "</section>"


def render_watchlist(items: list[dict[str, Any]], error: str | None) -> str:
    rows = []
    for item in items:
        rows.append(
            "<tr>"
            f"<td>{esc(item.get('code', '-'))}</td>"
            f"<td>{esc(item.get('name', '-'))}</td>"
            f"<td>{esc(item.get('market', '-'))}</td>"
            f"<td>{esc(item.get('note', ''))}</td>"
            "</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="4">暂无 enabled 股票。</td></tr>')
    note = f'<p class="muted">{esc(error)}</p>' if error else ""
    return f"""
<section>
  <h2>观察池 enabled 股票</h2>
  {note}
  <table>
    <thead><tr><th>代码</th><th>名称</th><th>市场</th><th>备注</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</section>"""


def render_news(items: list[dict[str, Any]]) -> str:
    parts = []
    for item in items[:10]:
        title = first_text(item, ["title"]) or first_text(raw_ref(item), ["title"]) or "-"
        publish_time = first_text(item, ["publish_time", "date"]) or first_text(raw_ref(item), ["publish_time", "date"])
        summary = first_text(item, ["summary"]) or first_text(raw_ref(item), ["summary"])
        url = first_text(item, ["url"]) or first_text(raw_ref(item), ["url"])
        link = f' <a href="{esc(url)}" target="_blank" rel="noreferrer">来源</a>' if url else ""
        parts.append(
            f'<li><span class="item-title">{esc(title)}</span>{link}'
            f'<div class="muted">{esc(format_datetime(publish_time))}</div>'
            f'<div>{esc(summary[:180])}</div></li>'
        )
    if not parts:
        parts.append("<li>暂无新闻证据。</li>")
    return f"<section><h2>最新新闻列表</h2><ul>{''.join(parts)}</ul></section>"


def render_stock_evidence(announcements: list[dict[str, Any]], reports: list[dict[str, Any]]) -> str:
    grouped = group_stock_evidence(announcements, reports)
    if not grouped:
        return "<section><h2>观察池个股证据</h2><p>暂无公告或研报证据。</p></section>"

    sections = []
    for (code, name, market), bucket in grouped.items():
        ann_html = "".join(
            f"<li>{esc(first_text(item, ['title']) or '-')}<div class=\"muted\">{esc(format_datetime(first_text(item, ['publish_time', 'date'])))}</div></li>"
            for item in bucket["announcements"][:5]
        ) or "<li>暂无公告证据。</li>"
        report_html = "".join(
            f"<li>{esc(first_text(item, ['title']) or '-')}<div class=\"muted\">{esc(format_datetime(first_text(item, ['publish_time', 'date'])))}</div></li>"
            for item in bucket["reports"][:5]
        ) or "<li>暂无研报证据。</li>"
        sections.append(
            f"""
<div class="panel">
  <h3>{esc(code)} {esc(name)} {esc(market)}</h3>
  <p class="muted">公告 {len(bucket["announcements"])} 条 / 研报 {len(bucket["reports"])} 条</p>
  <h3>公告证据</h3>
  <ul>{ann_html}</ul>
  <h3>研报证据</h3>
  <ul>{report_html}</ul>
</div>"""
        )
    return f"<section><h2>观察池个股证据</h2>{''.join(sections)}</section>"


def render_hot_events(payload: dict[str, Any] | None, error: str | None, compact: bool = False) -> str:
    if not payload:
        return f'<section><h2>热点事件分析</h2><p>{esc(error or "暂无热点分析输出。")}</p></section>'

    events = hot_events(payload)
    grouped = group_events_by_strength(events)
    sections: list[str] = [render_hot_overview(payload, events)]
    limit = 3 if compact else 999
    for strength in STRENGTH_ORDER:
        bucket = grouped[strength]
        visible = bucket[:limit]
        cards = "".join(render_event_card(event) for event in visible)
        if not cards:
            cards = '<div class="panel">暂无事件。</div>'
        more = ""
        if compact and len(bucket) > limit:
            more = f'<p class="muted">还有 {len(bucket) - limit} 条 {esc(strength)} 事件，打开热点分析详情查看。</p>'
        sections.append(
            f"""
<section>
  <h2>{esc(strength)} 热点事件</h2>
  {cards}
  {more}
</section>"""
        )
    return "\n".join(sections)


def render_hot_overview(payload: dict[str, Any] | None, events: list[dict[str, Any]]) -> str:
    counts = strength_counts(events)
    concepts = payload.get("matched_concepts", []) if payload else []
    concept_text = "、".join(
        f"{item.get('concept', '-')}({item.get('event_count', 0)})"
        for item in concepts
        if isinstance(item, dict)
    ) or "-"
    candidate_count = text_value(payload.get("candidate_watchlist_count")) if payload else "0"
    return f"""
<section>
  <h2>热点概览</h2>
  {render_stat_cards([
        ("热点事件总数", len(events)),
        ("high", counts["high"]),
        ("medium", counts["medium"]),
        ("low", counts["low"]),
        ("热点候选池数量", candidate_count or "0"),
    ])}
  <p>命中概念列表：{esc(concept_text)}</p>
  <p class="muted">本页读取本地 hot_events_latest.json，按 impact_strength 分组展示；candidate_watchlist 在页面中统一称为热点候选池。</p>
  <p><a href="/hot-events-report">打开 hot_events_latest.md 报告预览</a></p>
</section>"""


def render_candidate_review_overview(payload: dict[str, Any] | None, error: str | None) -> str:
    if not payload:
        return f'<section><h2>候选审核池 candidate_review</h2><div class="warning">warning: {esc(error or "暂无 candidate_review 输出。")}</div></section>'
    meta = candidate_review_meta(payload)
    buckets = candidate_review_buckets(payload)
    items = candidate_review_items(payload)
    item_count = meta.get("item_count", len(items))
    selected_count = meta.get("selected_count", len(selected_review_items(items)))
    blocked_count = meta.get("blocked_count", buckets.get("blocked", 0))
    skip_count = meta.get("skip_count", buckets.get("skip", 0))
    cards = [
        ("审核池条目", item_count),
        ("重点审核", selected_count),
        ("暂不纳入", skip_count),
        ("明确排除", blocked_count),
        ("生成时间", meta.get("created_at", "-"), "time"),
    ]
    bucket_parts = []
    for bucket in REVIEW_BUCKET_ORDER:
        count = buckets.get(bucket, 0)
        if count:
            bucket_parts.append(
                f'<a class="bucket-link" href="#bucket-{esc(bucket)}">{esc(REVIEW_BUCKET_LABELS.get(bucket, bucket))}<span>{esc(count)}</span></a>'
            )
    bucket_nav = '<div class="bucket-nav">' + "".join(bucket_parts) + "</div>" if bucket_parts else ""
    warning = f'<div class="warning">warning: {esc(error)}</div>' if error else ""
    return f"""
<section>
  <h2>候选审核池概览</h2>
  {warning}
  <p>candidate_review 是按用户偏好、热点和短期趋势二次筛选后的人工审核池；本页只读展示，不会自动同步到 watchlist。</p>
  {render_stat_cards(cards)}
  {bucket_nav}
  <div class="source-note">方法：<code>{esc(meta.get("method", "rule_based"))}</code>；同步模式：<code>{esc(meta.get("watchlist_sync_mode", "manual_confirm"))}</code>；输入候选：<code>{esc(meta.get("input_candidate_file", relative_path(CANDIDATE_REVIEW_JSON_PATH)))}</code></div>
  <p><a href="/candidate-review-report">打开 candidate_review_latest.md 报告预览</a></p>
</section>"""


def review_bucket_description(bucket: str) -> str:
    descriptions = {
        "core_watch": "优先看：命中强偏好主线，适合作为核心风向标或中军观察。",
        "elastic_watch": "重点看弹性：题材相关度较高，但波动和分歧可能更大。",
        "market_height_watch": "高度观察：更偏情绪高度或市场辨识度，重点观察持续性。",
        "trend_watch": "趋势观察：先看形态与量能修复，确认趋势后再提高优先级。",
        "skip": "暂不纳入：当前不符合偏好或交易性不足，保留记录但降低优先级。",
        "blocked": "明确排除：命中禁用/排除逻辑，默认不进入人工重点池。",
        "unknown": "信息不足：字段不完整或规则无法明确归类。",
    }
    return descriptions.get(bucket, "按规则分组的候选审核条目。")


def format_score(value: Any) -> str:
    text = text_value(value)
    if not text or text == "-":
        return "-"
    try:
        number = float(text)
    except ValueError:
        return text
    return f"{number:.2f}".rstrip("0").rstrip(".")


def review_list_items(values: Any) -> list[str]:
    if isinstance(values, list):
        return [ui_text(item) for item in values if ui_text(item) and ui_text(item) != "-"]
    text = ui_text(values)
    return [text] if text and text != "-" else []


def render_review_tags(values: Any, empty: str = "-") -> str:
    items = review_list_items(values)
    if not items:
        return f'<span class="muted">{esc(empty)}</span>'
    return '<div class="tag-list">' + "".join(f'<span class="pill">{esc(item)}</span>' for item in items) + "</div>"


def render_review_text_block(title: str, values: Any, empty: str = "-", class_name: str = "") -> str:
    items = review_list_items(values)
    if not items:
        body = f'<p class="muted">{esc(empty)}</p>'
    elif len(items) == 1:
        body = f'<p>{esc(items[0])}</p>'
    else:
        body = '<ul>' + "".join(f'<li>{esc(item)}</li>' for item in items) + '</ul>'
    extra_class = f" {class_name}" if class_name else ""
    return f'<div class="review-block{extra_class}"><h4>{esc(title)}</h4>{body}</div>'


def render_review_metric(label: str, value: Any, strong: bool = False) -> str:
    class_name = "review-metric strong" if strong else "review-metric"
    return f'<div class="{class_name}"><div class="label">{esc(label)}</div><div>{esc(value)}</div></div>'


def render_trend_metrics(item: dict[str, Any]) -> str:
    metrics = item.get("trend_metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}
    rows = [
        ("最新收盘", format_score(metrics.get("latest_close"))),
        ("1日涨跌", f'{format_score(metrics.get("pct_chg_1d"))}%'),
        ("5日涨跌", f'{format_score(metrics.get("pct_chg_5d"))}%'),
        ("量比5日", format_score(metrics.get("volume_ratio_5d"))),
        ("距20日高点", f'{format_score(metrics.get("distance_to_20d_high"))}%'),
        ("交易日", format_datetime(metrics.get("latest_trade_date"))),
    ]
    return '<div class="review-mini-metrics">' + "".join(
        f'<span><strong>{esc(label)}</strong>{esc(value)}</span>' for label, value in rows if text_value(value) and value != "-%"
    ) + '</div>'


def to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def daily_k_items(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not payload:
        return []
    items = payload.get("items", [])
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def build_daily_k_index(payload: dict[str, Any] | None) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for item in daily_k_items(payload):
        code = text_value(item.get("code")) or text_value(item.get("query_code"))
        bars = item.get("bars", [])
        if code and isinstance(bars, list):
            valid_bars = [bar for bar in bars if isinstance(bar, dict)]
            index[code] = valid_bars
    return index


def render_kline_volume_chart(bars: list[dict[str, Any]], limit: int = 20) -> str:
    recent = bars[-limit:] if bars else []
    raw: list[dict[str, Any]] = []
    previous_close: float | None = None
    for bar in recent:
        open_price = to_float(bar.get("open"))
        close_price = to_float(bar.get("close"))
        high_price = to_float(bar.get("high"))
        low_price = to_float(bar.get("low"))
        volume = to_float(bar.get("volume"))
        if None in (open_price, close_price, high_price, low_price, volume):
            continue
        raw_pct = to_float(bar.get("pct_chg"))
        pct_chg = raw_pct
        if pct_chg is None and previous_close not in (None, 0):
            pct_chg = (close_price - previous_close) / previous_close * 100
        raw.append(
            {
                "trade_date": text_value(bar.get("trade_date")),
                "raw_open": open_price,
                "raw_close": close_price,
                "raw_high": high_price,
                "raw_low": low_price,
                "volume": volume,
                "pct_chg": pct_chg,
                "previous_close": previous_close,
            }
        )
        previous_close = close_price
    if len(raw) < 2:
        return '<div class="chart-empty">暂无足够日 K 数据。</div>'

    # Display-layer qfq approximation: the local source is adjust_type=none, so we only
    # back-adjust earlier OHLC values around large discontinuities for visual continuity.
    adjusted = [dict(bar) for bar in raw]
    gap_notes: list[str] = []
    for idx in range(1, len(raw)):
        prev_close = raw[idx].get("previous_close")
        current_open = raw[idx].get("raw_open")
        if not isinstance(prev_close, float) or not prev_close or not isinstance(current_open, float):
            continue
        gap_pct = (current_open - prev_close) / prev_close * 100
        if abs(gap_pct) >= 15:
            factor = current_open / prev_close
            for prior in adjusted[:idx]:
                for key in ("open", "close", "high", "low"):
                    source_key = f"raw_{key}"
                    base = prior.get(key, prior.get(source_key))
                    if isinstance(base, float):
                        prior[key] = base * factor
            gap_notes.append(f'{raw[idx]["trade_date"]} 前复权折算 {format_score(factor)}x，原始跳空 {format_score(gap_pct)}%')
    for bar in adjusted:
        for key in ("open", "close", "high", "low"):
            bar.setdefault(key, bar.get(f"raw_{key}"))

    width = 640
    height = 260
    left = 40
    right = 14
    price_top = 16
    price_bottom = 156
    volume_top = 182
    volume_bottom = 228
    plot_width = width - left - right
    n = len(adjusted)
    closes = [bar["close"] for bar in adjusted]
    ma5_values: list[float | None] = []
    for idx in range(n):
        if idx >= 4:
            ma5_values.append(sum(closes[idx - 4 : idx + 1]) / 5)
        else:
            ma5_values.append(None)
    highs = [bar["high"] for bar in adjusted] + [value for value in ma5_values if value is not None]
    lows = [bar["low"] for bar in adjusted] + [value for value in ma5_values if value is not None]
    volumes = [bar["volume"] for bar in adjusted]
    price_max = max(highs)
    price_min = min(lows)
    if price_max == price_min:
        price_max += 1
        price_min -= 1
    volume_max = max(volumes) or 1

    def price_y(value: float) -> float:
        return price_top + (price_max - value) / (price_max - price_min) * (price_bottom - price_top)

    def volume_y(value: float) -> float:
        return volume_bottom - value / volume_max * (volume_bottom - volume_top)

    step = plot_width / n
    candle_width = max(4, min(14, step * 0.48))
    candles: list[str] = []
    volume_bars: list[str] = []
    hover_layers: list[str] = []
    gap_markers: list[str] = []
    ma5_points: list[str] = []
    for idx, bar in enumerate(adjusted):
        x = left + step * idx + step / 2
        open_y = price_y(bar["open"])
        close_y = price_y(bar["close"])
        high_y = price_y(bar["high"])
        low_y = price_y(bar["low"])
        top_y = min(open_y, close_y)
        body_height = max(1, abs(close_y - open_y))
        cls = "up" if bar["close"] >= bar["open"] else "down"
        ma5_value = ma5_values[idx]
        ma5_text = "-" if ma5_value is None else format_score(ma5_value)
        if ma5_value is not None:
            ma5_points.append(f'{x:.1f},{price_y(ma5_value):.1f}')
        pct_text = "-" if bar["pct_chg"] is None else f'{format_score(bar["pct_chg"])}%'
        title = (
            f'{bar["trade_date"]}\n'
            f'前复权开盘: {format_score(bar["open"])}\n'
            f'前复权收盘: {format_score(bar["close"])}\n'
            f'前复权最高: {format_score(bar["high"])}\n'
            f'前复权最低: {format_score(bar["low"])}\n'
            f'涨跌幅: {pct_text}\n'
            f'MA5: {ma5_text}\n'
            f'成交量: {format_score(bar["volume"])}\n'
            f'原始开/收: {format_score(bar["raw_open"])} / {format_score(bar["raw_close"])}'
        )
        candles.append(
            f'<g class="candle {cls}">'
            f'<line x1="{x:.1f}" y1="{high_y:.1f}" x2="{x:.1f}" y2="{low_y:.1f}" />'
            f'<rect x="{x - candle_width / 2:.1f}" y="{top_y:.1f}" width="{candle_width:.1f}" height="{body_height:.1f}" />'
            f'</g>'
        )
        vy = volume_y(bar["volume"])
        volume_bars.append(
            f'<rect class="volume-bar {cls}" x="{x - candle_width / 2:.1f}" y="{vy:.1f}" width="{candle_width:.1f}" height="{volume_bottom - vy:.1f}" />'
        )
        hover_layers.append(
            f'<g class="hover-slot"><title>{esc(title)}</title>'
            f'<line class="hover-cross" x1="{x:.1f}" y1="{price_top}" x2="{x:.1f}" y2="{volume_bottom}" />'
            f'<rect class="hover-band" x="{left + step * idx:.1f}" y="{price_top}" width="{step:.1f}" height="{volume_bottom - price_top}" />'
            f'</g>'
        )
        prev_close = raw[idx].get("previous_close")
        if isinstance(prev_close, float) and prev_close:
            gap_pct = (raw[idx]["raw_open"] - prev_close) / prev_close * 100
            if abs(gap_pct) >= 15:
                gap_markers.append(
                    f'<line class="gap-marker" x1="{x - step / 2:.1f}" y1="{price_top}" x2="{x - step / 2:.1f}" y2="{volume_bottom}" />'
                )
    ma5_line = ""
    if len(ma5_points) >= 2:
        ma5_line = f'<polyline class="ma-line" points="{" ".join(ma5_points)}" /><text class="ma-label" x="{width - right - 34}" y="{price_top + 12}">MA5</text>'
    grid_lines = "".join(
        f'<line class="chart-grid" x1="{left}" y1="{y}" x2="{width - right}" y2="{y}" />'
        for y in (price_top, (price_top + price_bottom) / 2, price_bottom, volume_top, volume_bottom)
    )
    first_date = adjusted[0]["trade_date"]
    last_date = adjusted[-1]["trade_date"]
    gap_note_html = ""
    if gap_notes:
        gap_note_html = f'<div class="chart-note">图表已按本地前复权口径展示：{esc("；".join(gap_notes[:2]))}</div>'
    else:
        gap_note_html = '<div class="chart-note muted">图表口径：前复权展示；成交量为原始成交量。</div>'
    return f"""
<div class="kline-chart" role="img" aria-label="最近 {len(adjusted)} 个交易日前复权 K 线和成交量">
  <svg viewBox="0 0 {width} {height}" preserveAspectRatio="none">
    {grid_lines}
    <text class="axis-label" x="2" y="20">{esc(format_score(price_max))}</text>
    <text class="axis-label" x="2" y="156">{esc(format_score(price_min))}</text>
    <text class="axis-label" x="2" y="186">VOL</text>
    {''.join(volume_bars)}
    {''.join(candles)}
    {ma5_line}
    {''.join(gap_markers)}
    {''.join(hover_layers)}
    <text class="date-label" x="{left}" y="252">{esc(first_date)}</text>
    <text class="date-label" x="{width - right}" y="252" text-anchor="end">{esc(last_date)}</text>
  </svg>
</div>{gap_note_html}"""


def render_candidate_review_card(
    item: dict[str, Any],
    status_index: dict[str, dict[str, Any]] | None = None,
    compact: bool = False,
    daily_k_index: dict[str, list[dict[str, Any]]] | None = None,
    weekly_k_index: dict[str, list[dict[str, Any]]] | None = None,
) -> str:
    selected = item.get("selected_for_review") is True
    status_item = (status_index or {}).get(text_value(item.get("code")), {})
    manual_status = text_value(status_item.get("status")) or "pending"
    confirmed_by_user = status_item.get("confirmed_by_user")
    if not isinstance(confirmed_by_user, bool):
        confirmed_by_user = False
    review_note = text_value(status_item.get("review_note")) or "-"
    status_updated_at = format_datetime(status_item.get("updated_at"))
    bucket = text_value(item.get("review_bucket")) or "unknown"
    bucket_label = REVIEW_BUCKET_LABELS.get(bucket, bucket)
    trend_state = text_value(item.get("trend_state")) or "unknown"
    trend_label = TREND_STATE_LABELS.get(trend_state, trend_state)
    manual_confirm = item.get("manual_confirm_required", True)
    selected_label = "重点审核" if selected else "非重点"
    header_meta = f"{text_value(item.get('market')) or '-'} · {bucket_label} · {trend_label}"
    status_detail = "" if compact else f"""
      <div class="review-block">
        <h4>人工状态</h4>
        <div class="review-mini-metrics">
          <span><strong>status</strong>{esc(manual_status)}</span>
          <span><strong>confirmed</strong>{esc(confirmed_by_user)}</span>
          <span><strong>updated</strong>{esc(status_updated_at)}</span>
        </div>
        <p class="muted">{esc(review_note)}</p>
      </div>"""
    code = text_value(item.get("code"))
    kline_chart = render_candidate_kline_tabs(code, daily_k_index, weekly_k_index)
    details = "" if compact else f"""
    <div class="review-sections">
      <div class="review-block theme-block">
        <h4>主题与角色</h4>
        <div class="theme-fields">
          <div class="review-field"><span>强偏好</span>{render_review_tags(item.get("matched_preferred_themes"))}</div>
          <div class="review-field"><span>轻观察</span>{render_review_tags(item.get("matched_watch_themes"))}</div>
          <div class="review-field"><span>相关概念</span>{render_review_tags(item.get("related_concepts"))}</div>
          <div class="review-field"><span>候选角色</span>{render_review_tags(item.get("candidate_roles"))}</div>
        </div>
      </div>
      <div class="review-block trend-block">
        <h4>趋势状态</h4>
        {render_trend_metrics(item)}
        {kline_chart}
        <p>{esc(ui_text(item.get("trend_reason", "-")))}</p>
      </div>
      <div class="review-subgrid">
        {render_review_text_block("入选 / 分组理由", [item.get("bucket_reason"), item.get("selection_note"), item.get("filter_reason")])}
        {render_review_text_block("风险与观察", review_list_items(item.get("risk_notes")) + review_list_items(item.get("observation_notes")))}
        {render_review_text_block("来源事件", item.get("source_event_titles"))}
        {status_detail}
      </div>
    </div>"""
    compact_reason = "" if not compact else f'<p class="muted">{esc(ui_text(item.get("bucket_reason", "-")))}</p>'
    return f"""
<article class="event-card review-card">
  <div class="review-card-head">
    <div>
      <h3>{esc(item.get("name", "-"))} {esc(item.get("code", "-"))}</h3>
      <p class="muted">{esc(header_meta)}</p>
    </div>
    <div class="score-box">
      <div class="label">final_score</div>
      <div>{esc(format_score(item.get("final_score", "-")))}</div>
    </div>
  </div>
  <div class="event-meta">
    <span class="badge">{esc(selected_label)}</span>
    <span class="pill">review_bucket: {esc(bucket_label)}</span>
    <span class="pill">trend_state: {esc(trend_label)}</span>
    <span class="pill">manual_status: {esc(manual_status)}</span>
    <span class="pill">manual_confirm_required: {esc(manual_confirm)}</span>
  </div>
  <div class="review-metrics">
    {render_review_metric("热度", format_score(item.get("raw_heat_score")))}
    {render_review_metric("偏好", format_score(item.get("preference_score")))}
    {render_review_metric("趋势", format_score(item.get("trend_score")))}
    {render_review_metric("风险扣分", format_score(item.get("risk_penalty")))}
  </div>
  {compact_reason}
  {details}
</article>"""


def render_candidate_review_selected(
    items: list[dict[str, Any]],
    compact: bool = False,
    status_index: dict[str, dict[str, Any]] | None = None,
) -> str:
    selected = selected_review_items(items)
    visible = selected[:4] if compact else selected[:6]
    cards = "".join(render_candidate_review_card(item, status_index=status_index, compact=True) for item in visible)
    if not cards:
        cards = '<div class="panel">暂无重点审核条目。</div>'
    more = ""
    if len(selected) > len(visible):
        more = f'<p class="muted">还有 {len(selected) - len(visible)} 条重点审核条目，可在下方分组里继续查看。</p>'
    return f"""
<section>
  <h2>重点审核名单</h2>
  <p class="muted">仅展示 selected_for_review=true 的条目；这里只读展示，仍需人工判断。</p>
  <div class="review-card-grid">{cards}</div>
  {more}
</section>"""


def render_candidate_review_buckets(
    items: list[dict[str, Any]],
    compact: bool = False,
    status_index: dict[str, dict[str, Any]] | None = None,
    daily_k_index: dict[str, list[dict[str, Any]]] | None = None,
    weekly_k_index: dict[str, list[dict[str, Any]]] | None = None,
) -> str:
    sections: list[str] = []
    per_bucket_limit = 1 if compact else 999
    for bucket in REVIEW_BUCKET_ORDER:
        bucket_items = [item for item in items if text_value(item.get("review_bucket")) == bucket]
        if not bucket_items:
            continue
        visible = bucket_items[:per_bucket_limit]
        selected_count = sum(1 for item in bucket_items if item.get("selected_for_review") is True)
        cards = "".join(render_candidate_review_card(item, status_index=status_index, compact=compact, daily_k_index=daily_k_index, weekly_k_index=weekly_k_index) for item in visible)
        more = ""
        if len(bucket_items) > len(visible):
            more = f'<p class="muted">还有 {len(bucket_items) - len(visible)} 条 {esc(REVIEW_BUCKET_LABELS.get(bucket, bucket))} 条目。</p>'
        sections.append(
            f"""
<section class="review-bucket" id="bucket-{esc(bucket)}">
  <div class="bucket-title-row">
    <div>
      <h2>{esc(REVIEW_BUCKET_LABELS.get(bucket, bucket))}</h2>
      <p class="muted">{esc(review_bucket_description(bucket))}</p>
    </div>
    <div class="bucket-counts">
      <span class="pill">数量: {esc(len(bucket_items))}</span>
      <span class="pill">重点: {esc(selected_count)}</span>
      <span class="pill">bucket: {esc(bucket)}</span>
    </div>
  </div>
  {cards}
  {more}
</section>"""
        )
    if not sections:
        return '<section><h2>分组审核列表</h2><div class="panel">暂无候选审核条目。</div></section>'
    return "\n".join(sections)


def render_candidate_review(
    payload: dict[str, Any] | None,
    error: str | None,
    compact: bool = False,
    status_payload: dict[str, Any] | None = None,
) -> str:
    if not payload:
        return render_candidate_review_overview(payload, error)
    items = candidate_review_items(payload)
    status_index = build_review_status_index(status_payload)
    daily_k_payload, daily_k_error = read_json(DAILY_K_PATH)
    weekly_k_payload, weekly_k_error = read_json(WEEKLY_K_PATH)
    daily_k_index = build_daily_k_index(daily_k_payload)
    weekly_k_index = build_daily_k_index(weekly_k_payload)
    health_errors = payload.get("errors", [])
    error_rows = ""
    if isinstance(health_errors, list) and health_errors:
        error_rows = '<section class="warning"><h2>数据健康 / errors</h2><ul>' + "".join(
            f"<li>{esc(item)}</li>" for item in health_errors
        ) + "</ul></section>"
    if daily_k_error and not compact:
        error_rows += f'<section class="warning"><h2>日 K 数据 warning</h2><p>{esc(daily_k_error)}</p></section>'
    if weekly_k_error and not compact:
        error_rows += f'<section class="warning"><h2>周 K 数据 warning</h2><p>{esc(weekly_k_error)}</p></section>'
    if compact:
        return f"""
{render_candidate_review_overview(payload, error)}
{render_candidate_review_selected(items, compact=True, status_index=status_index)}
{error_rows}"""
    return f"""
{render_candidate_review_overview(payload, error)}
{render_review_concept_note()}
{render_candidate_review_selected(items, compact=False, status_index=status_index)}
{render_candidate_review_buckets(items, compact=False, status_index=status_index, daily_k_index=daily_k_index, weekly_k_index=weekly_k_index)}
{error_rows}
<section>
  <h2>免责声明</h2>
  <p class="disclaimer">{esc(DISCLAIMER)}</p>
</section>"""


def daily_report_meta(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}
    meta = payload.get("meta", {})
    return meta if isinstance(meta, dict) else {}


def daily_report_list(payload: dict[str, Any] | None, key: str) -> list[dict[str, Any]]:
    if not payload:
        return []
    items = payload.get(key, [])
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def daily_report_text_list(payload: dict[str, Any] | None, key: str) -> list[str]:
    if not payload:
        return []
    items = payload.get(key, [])
    return [text_value(item) for item in items if text_value(item)] if isinstance(items, list) else []


def render_daily_status_summary(summary: Any) -> str:
    if not isinstance(summary, dict):
        summary = {}
    rows = [
        f'<span class="pill">{esc(status)}: {esc(summary.get(status, 0))}</span>'
        for status in ["pending", "watch", "skip", "confirmed", "rejected"]
    ]
    return '<div class="event-meta">' + "".join(rows) + "</div>"


def render_daily_report_overview(payload: dict[str, Any] | None, error: str | None) -> str:
    if not payload:
        return f'<section><h2>盘后报告摘要</h2><div class="warning">warning: {esc(error or "暂无盘后报告输出。")}</div></section>'
    meta = daily_report_meta(payload)
    market_summary = payload.get("market_summary", {})
    if not isinstance(market_summary, dict):
        market_summary = {}
    hot_count = len(daily_report_list(payload, "hot_mainlines"))
    selected_count = len(daily_report_list(payload, "selected_candidates"))
    cards = [
        ("created_at", meta.get("created_at", "-"), "time"),
        ("hot_mainlines", hot_count),
        ("selected_candidates", selected_count),
        ("candidate_review_count", market_summary.get("candidate_review_count", "-")),
    ]
    warning = f'<div class="warning">warning: {esc(error)}</div>' if error else ""
    return f"""
<section>
  <h2>盘后报告摘要</h2>
  {warning}
  <p>rule_based 盘后整理，研究辅助，不自动写入 watchlist。</p>
  {render_stat_cards(cards)}
  {render_daily_status_summary(payload.get("manual_status_summary", {}))}
  <p><a href="/daily-report">打开盘后报告页面</a> · <a href="/daily-report-report">打开 Markdown 报告预览</a></p>
</section>"""


def render_daily_mainlines(payload: dict[str, Any] | None, compact: bool = False) -> str:
    items = daily_report_list(payload, "hot_mainlines")
    limit = 3 if compact else 999
    cards = ""
    for item in items[:limit]:
        cards += f"""
<article class="event-card">
  <h3>{esc(item.get("title", "-"))}</h3>
  <div class="event-meta">
    <span class="pill">impact_strength: {esc(item.get("impact_strength", "-"))}</span>
    <span class="pill">impact_score: {esc(item.get("impact_score", "-"))}</span>
  </div>
  <p class="muted">risk_notes: {esc(ui_text(join_values(item.get("risk_notes"))))}</p>
</article>"""
    if not cards:
        cards = '<div class="panel">暂无热点主线。</div>'
    return f"<section><h2>今日热点主线</h2>{cards}</section>"


def render_daily_selected(payload: dict[str, Any] | None, compact: bool = False) -> str:
    items = daily_report_list(payload, "selected_candidates")
    limit = 4 if compact else 999
    cards = ""
    for item in items[:limit]:
        cards += f"""
<article class="event-card">
  <h3>{esc(item.get("name", "-"))} {esc(item.get("code", "-"))}</h3>
  <div class="event-meta">
    <span class="pill">review_bucket: {esc(item.get("review_bucket", "-"))}</span>
    <span class="pill">final_score: {esc(item.get("final_score", "-"))}</span>
    <span class="pill">trend_state: {esc(item.get("trend_state", "-"))}</span>
    <span class="pill">manual_status: {esc(item.get("manual_status", "pending"))}</span>
  </div>
  <div class="detail-grid">
    <div class="detail-label">review_note</div><div>{esc(item.get("review_note", "-"))}</div>
    <div class="detail-label">bucket_reason</div><div>{esc(item.get("bucket_reason", "-"))}</div>
  </div>
</article>"""
    if not cards:
        cards = '<div class="panel">暂无重点审核条目。</div>'
    return f"<section><h2>重点审核名单</h2>{cards}</section>"


def render_daily_wind_vane(payload: dict[str, Any] | None, compact: bool = False) -> str:
    items = daily_report_list(payload, "wind_vane_table")
    limit = 6 if compact else 999
    cards = ""
    for item in items[:limit]:
        cards += f"""
<article class="event-card">
  <h3>{esc(item.get("name", "-"))} {esc(item.get("code", "-"))}</h3>
  <div class="event-meta">
    <span class="pill">layer: {esc(item.get("layer", "-"))}</span>
    <span class="pill">trend_state: {esc(item.get("trend_state", "-"))}</span>
    <span class="pill">manual_status: {esc(item.get("manual_status", "pending"))}</span>
  </div>
  <p>{esc(item.get("focus_reason", "-"))}</p>
</article>"""
    if not cards:
        cards = '<div class="panel">暂无风向标条目。</div>'
    return f"<section><h2>风向标股票表</h2>{cards}</section>"


def render_daily_text_section(title: str, values: list[str]) -> str:
    if not values:
        return f"<section><h2>{esc(title)}</h2><div class=\"panel\">暂无。</div></section>"
    rows = "".join(f"<li>{esc(value)}</li>" for value in values)
    return f"<section><h2>{esc(title)}</h2><ul>{rows}</ul></section>"


def render_daily_report(payload: dict[str, Any] | None, error: str | None, compact: bool = False) -> str:
    if not payload:
        return render_daily_report_overview(payload, error)
    if compact:
        return render_daily_report_overview(payload, error)
    errors = payload.get("errors", [])
    error_rows = ""
    if isinstance(errors, list) and errors:
        error_rows = '<section class="warning"><h2>数据健康 / errors</h2><ul>' + "".join(
            f"<li>{esc(item)}</li>" for item in errors
        ) + "</ul></section>"
    return f"""
{render_daily_report_overview(payload, error)}
{render_daily_mainlines(payload, compact=False)}
{render_daily_selected(payload, compact=False)}
<section><h2>人工审核状态汇总</h2>{render_daily_status_summary(payload.get("manual_status_summary", {}))}</section>
{render_daily_wind_vane(payload, compact=False)}
{render_daily_text_section("明日观察重点", daily_report_text_list(payload, "tomorrow_watch"))}
{render_daily_text_section("风险提示", daily_report_text_list(payload, "risk_notes"))}
<section><h2>Markdown 报告入口</h2><p><a href="/daily-report-report">打开 daily_after_close_report_latest.md 报告预览</a></p></section>
{error_rows}
<section>
  <h2>免责声明</h2>
  <p class="disclaimer">{esc(DISCLAIMER)}</p>
</section>"""


def trend_items(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not payload:
        return []
    items = payload.get("items", [])
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def normalize_trend_state(value: Any) -> str:
    text = text_value(value)
    return text if text in TREND_STATE_ORDER else "unknown"


def trend_state_label(value: Any) -> str:
    state = normalize_trend_state(value)
    return f"{state} / {TREND_STATE_LABELS.get(state, '数据不足')}"


def metric_value(metrics: dict[str, Any], key: str) -> str:
    value = metrics.get(key)
    return "-" if value in (None, "") else text_value(value)


def render_trend_missing(error: str | None) -> str:
    reason = error or f"missing: {relative_path(TREND_ANALYSIS_JSON_PATH)}"
    return f"""
<section>
  <h2>短期趋势分析</h2>
  <div class="warning">
    <strong>暂未生成趋势分析数据</strong>
    <p>{esc(reason)}</p>
    <p>请先运行：</p>
    <pre>python scripts/probes/test_daily_k_probe.py --limit 10
python scripts/analysis/analyze_trends.py</pre>
  </div>
</section>"""


def render_trend_overview(payload: dict[str, Any], items: list[dict[str, Any]], error: str | None) -> str:
    meta = payload.get("meta", {})
    if not isinstance(meta, dict):
        meta = {}
    counts = meta.get("state_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    cards = [
        ("样本数量", meta.get("item_count", len(items))),
        ("可分析数量", meta.get("ok_count", "-")),
        ("数据不足", counts.get("unknown", 0)),
        ("报告时间", meta.get("created_at", "-")),
    ]
    state_rows = "".join(
        f'<span class="pill">{esc(state)} / {esc(TREND_STATE_LABELS[state])}: {esc(counts.get(state, 0))}</span>'
        for state in TREND_STATE_ORDER
    )
    warning = f'<div class="warning">warning: {esc(error)}</div>' if error else ""
    return f"""
<section>
  <h2>短期趋势分析概览</h2>
  {warning}
  {render_stat_cards(cards)}
  <div class="event-meta">{state_rows}</div>
  <p>数据来源：{esc(meta.get("source_file", relative_path(TREND_ANALYSIS_JSON_PATH)))}</p>
  <p>分析方法：{esc(meta.get("method", "rule_based"))}</p>
  <p><a href="/trend-analysis-report">打开 trend_analysis_latest.md 报告预览</a></p>
</section>"""


def render_trend_card(item: dict[str, Any]) -> str:
    metrics = item.get("metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}
    quality = item.get("data_quality", {})
    if not isinstance(quality, dict):
        quality = {}
    metric_keys = [
        "latest_close",
        "ma5",
        "ma10",
        "ma20",
        "pct_chg_1d",
        "pct_chg_5d",
        "pct_chg_10d",
        "volume_ratio_5d",
        "drawdown_from_20d_high",
    ]
    metric_rows = "".join(
        f"<tr><th>{esc(key)}</th><td>{esc(metric_value(metrics, key))}</td></tr>"
        for key in metric_keys
    )
    quality_text = (
        f"status={text_value(quality.get('status')) or '-'}; "
        f"bar_count={text_value(quality.get('bar_count')) or '-'}; "
        f"problems={join_values(quality.get('problems'))}"
    )
    return f"""
<article class="event-card">
  <h3>{esc(item.get("name", "-"))} {esc(item.get("code", "-"))}</h3>
  <div class="event-meta">
    <span class="pill">heat_score: {esc(item.get("heat_score", "-"))}</span>
    <span class="pill">trend_state: {esc(trend_state_label(item.get("trend_state")))}</span>
    <span class="pill">trend_score: {esc(item.get("trend_score", "-"))}</span>
    <span class="pill">latest_trade_date: {esc(item.get("latest_trade_date", "-"))}</span>
  </div>
  <div class="detail-grid">
    <div class="detail-label">market</div><div>{esc(item.get("market", "-"))}</div>
    <div class="detail-label">related_concepts</div><div>{esc(join_values(item.get("related_concepts")))}</div>
    <div class="detail-label">trend_reason</div><div>{esc(item.get("trend_reason", "-"))}</div>
    <div class="detail-label">trigger_conditions</div><div>{esc(join_values(item.get("trigger_conditions")))}</div>
    <div class="detail-label">risk_notes</div><div>{esc(ui_text(join_values(item.get("risk_notes"))))}</div>
    <div class="detail-label">observation_notes</div><div>{esc(ui_text(join_values(item.get("observation_notes"))))}</div>
    <div class="detail-label">data_quality</div><div>{esc(quality_text)}</div>
  </div>
  <h3>关键 metrics</h3>
  <table>
    <tbody>{metric_rows}</tbody>
  </table>
</article>"""


def render_trend_analysis(payload: dict[str, Any] | None, error: str | None, compact: bool = False) -> str:
    if not payload:
        return render_trend_missing(error)
    items = trend_items(payload)
    limit = 5 if compact else 999
    cards = "".join(render_trend_card(item) for item in items[:limit])
    if not cards:
        cards = '<div class="panel">暂无趋势分析条目。</div>'
    more = ""
    if compact and len(items) > limit:
        more = f'<p class="muted">还有 {len(items) - limit} 个趋势分析条目，打开详情页查看。</p>'
    return f"""
{render_trend_overview(payload, items, error)}
<section>
  <h2>短期趋势分析列表</h2>
  {cards}
  {more}
</section>"""


def render_fast_report_summary(text: str, error: str | None) -> str:
    if error:
        return f'<section><h2>Fast Report</h2><p>{esc(error)}</p></section>'
    lines = [line for line in text.splitlines() if line.strip()][:16]
    return f"""
<section>
  <h2>Fast Report 入口</h2>
  <p><a href="/fast-report">查看 fast_report_latest.md 内容摘要</a></p>
  <pre>{esc(chr(10).join(lines))}</pre>
</section>"""


def markdown_table_cells(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def is_markdown_table_separator(line: str) -> bool:
    cells = markdown_table_cells(line)
    return bool(cells) and all(cell and set(cell) <= {"-", ":", " "} for cell in cells)


def is_markdown_table_start(lines: list[str], index: int) -> bool:
    return (
        index + 1 < len(lines)
        and "|" in lines[index]
        and "|" in lines[index + 1]
        and is_markdown_table_separator(lines[index + 1])
    )


def render_markdown_table(lines: list[str], start: int) -> tuple[str, int]:
    headers = markdown_table_cells(lines[start])
    index = start + 2
    rows: list[list[str]] = []
    while index < len(lines) and "|" in lines[index] and lines[index].strip():
        rows.append(markdown_table_cells(lines[index]))
        index += 1
    header_html = "".join(f"<th>{esc(cell)}</th>" for cell in headers)
    body_rows = []
    for row in rows:
        padded = row + [""] * max(0, len(headers) - len(row))
        body_rows.append("<tr>" + "".join(f"<td>{esc(cell)}</td>" for cell in padded[: len(headers)]) + "</tr>")
    return (
        f"<table><thead><tr>{header_html}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>",
        index,
    )


def ordered_list_marker(line: str) -> tuple[bool, str]:
    stripped = line.lstrip()
    marker, _, rest = stripped.partition(". ")
    return (marker.isdigit() and bool(rest), rest)


def render_markdown_text(text: str) -> str:
    lines = ui_text(text).splitlines()
    parts: list[str] = []
    paragraph: list[str] = []
    index = 0

    def flush_paragraph() -> None:
        if paragraph:
            parts.append(f"<p>{esc(' '.join(paragraph))}</p>")
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            index += 1
            code_lines = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            parts.append(f"<pre><code>{esc(chr(10).join(code_lines))}</code></pre>")
            continue

        if not stripped:
            flush_paragraph()
            index += 1
            continue

        if is_markdown_table_start(lines, index):
            flush_paragraph()
            table_html, index = render_markdown_table(lines, index)
            parts.append(table_html)
            continue

        if stripped.startswith("### "):
            flush_paragraph()
            parts.append(f"<h3>{esc(stripped[4:].strip())}</h3>")
            index += 1
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            parts.append(f"<h2>{esc(stripped[3:].strip())}</h2>")
            index += 1
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            parts.append(f"<h1>{esc(stripped[2:].strip())}</h1>")
            index += 1
            continue

        if stripped.startswith(("- ", "* ")):
            flush_paragraph()
            items = []
            while index < len(lines):
                item = lines[index].strip()
                if not item.startswith(("- ", "* ")):
                    break
                items.append(f"<li>{esc(item[2:].strip())}</li>")
                index += 1
            parts.append(f"<ul>{''.join(items)}</ul>")
            continue

        is_ordered, ordered_text = ordered_list_marker(line)
        if is_ordered:
            flush_paragraph()
            items = []
            while index < len(lines):
                is_item, item_text = ordered_list_marker(lines[index])
                if not is_item:
                    break
                items.append(f"<li>{esc(item_text.strip())}</li>")
                index += 1
            parts.append(f"<ol>{''.join(items)}</ol>")
            continue

        paragraph.append(stripped)
        index += 1

    flush_paragraph()
    return '<div class="markdown-body">' + "\n".join(parts) + "</div>"


def render_markdown_page(path: Path, title: str) -> bytes:
    text, error = read_text(path)
    header = render_page_header(title, "本地 Markdown 报告预览，已转成易读排版。", relative_path(path))
    if error:
        body = f"""
{header}
<section class="warning"><strong>数据健康 warning</strong><p>{esc(error)}</p></section>
<section>
  <h2>免责声明</h2>
  <p class="disclaimer">{esc(DISCLAIMER)}</p>
</section>"""
    else:
        body = f"""
{header}
<section class="panel">
  <div class="source-note">读取 Markdown：<code>{esc(relative_path(path))}</code></div>
</section>
{render_markdown_text(text)}
<section>
  <h2>免责声明</h2>
  <p class="disclaimer">{esc(DISCLAIMER)}</p>
</section>"""
    return render_page(title, body)


def render_page_header(title: str, subtitle: str, source: str, readonly: bool = True, actions: list[tuple[str, str]] | None = None) -> str:
    action_html = ""
    if actions:
        action_html = '<div class="page-actions">' + "".join(
            f'<a class="button" href="{esc(href)}">{esc(label)}</a>' for label, href in actions
        ) + "</div>"
    mode = "只读展示" if readonly else "本地工具"
    return f"""
<section class="page-hero">
  <div>
    <div class="eyebrow">AStockFastLane Research Console</div>
    <h2>{esc(title)}</h2>
    <p>{esc(subtitle)}</p>
    <div class="event-meta">
      <span class="pill">读取：{esc(source)}</span>
      <span class="pill">{esc(mode)}</span>
      <span class="pill">研究辅助，不构成投资建议</span>
    </div>
  </div>
  {action_html}
</section>"""


def render_page(title: str, body: str) -> bytes:
    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4f6f8;
      --surface: #ffffff;
      --surface-soft: #f8fafc;
      --text: #18212f;
      --muted: #657386;
      --line: #d9e0e8;
      --accent: #126a6f;
      --accent-2: #315f8c;
      --accent-soft: #e8f4f4;
      --warn: #8a5a12;
      --warn-soft: #fff7e8;
      --bad: #9d2424;
      --bad-soft: #fff0f0;
      --shadow: 0 8px 22px rgba(20, 35, 55, 0.06);
      --sidebar-width: 264px;
      --main-width: calc(100vw - var(--sidebar-width) - 48px);
      --content-left: calc(var(--sidebar-width) + 24px);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.58;
    }}
    .brand-row {{ display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }}
    h1 {{ margin: 0 0 4px; font-size: 24px; letter-spacing: 0; }}
    h2 {{ margin: 0 0 10px; font-size: 22px; letter-spacing: 0; }}
    h3 {{ margin: 0 0 8px; font-size: 16px; letter-spacing: 0; }}
    p {{ margin: 8px 0; }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    main {{
      width: var(--main-width);
      max-width: none;
      margin: 24px 24px 48px var(--content-left);
    }}
    section {{ margin: 18px 0; }}
    .muted {{ color: var(--muted); }}
    .eyebrow {{ color: var(--accent); font-size: 12px; font-weight: 700; letter-spacing: 0; text-transform: uppercase; }}
    .side-nav {{
      position: fixed;
      left: 0;
      top: 0;
      bottom: 0;
      z-index: 40;
      width: var(--sidebar-width);
      pointer-events: auto;
    }}
    .side-nav-panel {{
      width: 100%;
      min-height: 100vh;
      height: 100vh;
      padding: 22px 18px 18px;
      background: linear-gradient(180deg, #ffffff 0%, #f8fbfc 100%);
      border-right: 1px solid var(--line);
      box-shadow: 8px 0 24px rgba(20, 35, 55, 0.05);
      overflow-y: auto;
    }}
    .side-tab {{ display: none; }}
    .side-brand {{
      padding: 4px 2px 18px;
      border-bottom: 1px solid var(--line);
      margin-bottom: 18px;
    }}
    .side-brand-title {{ margin: 0; font-size: 21px; font-weight: 800; color: var(--text); letter-spacing: -0.3px; }}
    .side-brand-subtitle {{ margin: 5px 0 0; color: var(--muted); font-size: 13px; line-height: 1.4; }}
    .side-nav-title {{ font-size: 12px; color: var(--muted); margin: 0 0 10px; text-transform: uppercase; letter-spacing: 0.06em; }}
    .toolbar {{ display: flex; flex-direction: column; gap: 10px; margin-top: 0; }}
    .side-nav .button {{
      width: 100%;
      justify-content: flex-start;
      min-height: 42px;
      padding: 9px 12px;
      border-radius: 10px;
      background: transparent;
      font-size: 15px;
      font-weight: 650;
    }}
    .side-nav .button::before {{
      content: "";
      width: 7px;
      height: 7px;
      border-radius: 999px;
      margin-right: 10px;
      background: #c8d5de;
      flex: 0 0 auto;
    }}
    .side-nav .button:hover {{ background: var(--accent-soft); border-color: #b9dddd; color: var(--accent); text-decoration: none; }}
    .side-footer {{
      position: absolute;
      left: 18px;
      right: 18px;
      bottom: 18px;
      padding-top: 14px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }}
    .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 34px;
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 6px 10px;
      background: var(--surface-soft);
      color: var(--text);
      font-size: 14px;
      white-space: nowrap;
    }}
    .button:hover {{ border-color: var(--accent); background: var(--accent-soft); text-decoration: none; }}
    .page-hero {{
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: flex-start;
      padding: 18px;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }}
    .page-actions {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }}
    .console-grid {{ display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.65fr); gap: 14px; align-items: start; }}
    .panel, .summary-card {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      box-shadow: var(--shadow);
    }}
    .summary-card {{ min-height: 112px; }}
    .stat {{ font-size: 26px; line-height: 1.1; font-weight: 750; }}
    .stat-time {{ font-size: 18px; line-height: 1.35; white-space: nowrap; }}
    .stat-text {{ font-size: 18px; line-height: 1.35; font-weight: 650; overflow-wrap: anywhere; }}
    .stat-path {{ font-family: Consolas, "Courier New", monospace; font-size: 13px; line-height: 1.35; font-weight: 500; overflow-wrap: anywhere; }}
    .label {{ color: var(--muted); font-size: 13px; }}
    .source-note {{
      color: var(--muted);
      font-size: 13px;
      overflow-wrap: anywhere;
    }}
    code {{
      font-family: Consolas, "Courier New", monospace;
      font-size: 0.94em;
      background: var(--surface-soft);
      border: 1px solid var(--line);
      border-radius: 5px;
      padding: 1px 4px;
    }}
    .event-card {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      margin: 10px 0;
      box-shadow: var(--shadow);
      overflow-wrap: anywhere;
    }}
    .review-card {{ padding: 16px; }}
    .review-card-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .review-card-head, .bucket-title-row {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: flex-start;
    }}
    .score-box {{
      min-width: 96px;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--accent-soft);
      color: var(--accent);
      text-align: center;
      font-size: 24px;
      font-weight: 750;
      line-height: 1.15;
    }}
    .review-metrics, .review-mini-metrics {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 10px 0;
    }}
    .review-metric, .review-mini-metrics span {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface-soft);
      padding: 7px 9px;
      min-width: 88px;
      font-size: 13px;
    }}
    .review-metric div:last-child {{ font-size: 18px; font-weight: 720; }}
    .review-mini-metrics span strong {{
      display: block;
      color: var(--muted);
      font-weight: 500;
      margin-bottom: 2px;
    }}
    .review-sections {{ display: grid; grid-template-columns: minmax(260px, 2fr) minmax(0, 3fr); gap: 12px; margin-top: 12px; align-items: stretch; }}
    .review-block {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface-soft);
      padding: 15px 16px;
      font-size: 15px;
      line-height: 1.75;
    }}
    .review-block h4 {{ margin: 0 0 10px; font-size: 16px; color: var(--accent-2); }}
    .review-block p {{ margin: 8px 0; }}
    .theme-block {{
      grid-column: 1;
      height: 100%;
      min-height: 360px;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
      gap: 12px;
    }}
    .theme-block h4 {{ font-size: 22px; margin-bottom: 6px; }}
    .theme-fields {{
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 18px;
      padding: 4px 0 8px;
    }}
    .trend-block {{ grid-column: 2; height: 100%; }}
    .review-subgrid {{ grid-column: 1 / -1; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .review-subgrid .review-block {{ height: 100%; }}
    .kline-chart {{
      width: 100%;
      height: 260px;
      margin: 10px 0 8px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      overflow: hidden;
    }}
    .kline-chart svg {{ width: 100%; height: 100%; display: block; }}
    .chart-grid {{ stroke: var(--line); stroke-width: 1; }}
    .axis-label, .date-label {{ fill: var(--muted); font-size: 11px; }}
    .hover-band {{ fill: transparent; cursor: crosshair; pointer-events: all; }}
    .hover-cross {{ stroke: var(--accent-2); stroke-width: 1; stroke-dasharray: 3 3; opacity: 0; pointer-events: none; }}
    .hover-slot:hover .hover-cross {{ opacity: 0.78; }}
    .gap-marker {{ stroke: var(--warn); stroke-width: 1.2; stroke-dasharray: 5 4; opacity: 0.85; }}
    .ma-line {{ fill: none; stroke: var(--accent-2); stroke-width: 1.6; opacity: 0.9; }}
    .ma-label {{ fill: var(--accent-2); font-size: 11px; font-weight: 700; }}
    .chart-note {{ margin-top: 6px; color: var(--warn); font-size: 12px; }}
    .candle line {{ stroke-width: 1.4; }}
    .candle rect {{ stroke-width: 1.1; }}
    .candle.up line, .candle.up rect {{ stroke: #b42318; fill: #fff7f6; }}
    .candle.down line, .candle.down rect {{ stroke: #087443; fill: #ecfdf3; }}
    .volume-bar {{ opacity: 0.38; }}
    .volume-bar.up {{ fill: #b42318; }}
    .volume-bar.down {{ fill: #087443; }}
    .chart-empty {{
      margin: 10px 0;
      padding: 12px;
      border: 1px dashed var(--line);
      border-radius: 8px;
      color: var(--muted);
      background: var(--surface);
      font-size: 13px;
    }}
    .candidate-card {{ padding: 16px; }}
    .candidate-card-layout {{ display: grid; grid-template-columns: minmax(320px, 0.45fr) minmax(420px, 0.55fr); gap: 16px; align-items: stretch; }}
    .candidate-info-panel, .candidate-chart-panel {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface-soft);
      padding: 14px;
      min-width: 0;
    }}
    .candidate-chart-panel {{ display: flex; flex-direction: column; align-self: stretch; min-height: 360px; }}
    .candidate-info-grid {{ display: grid; grid-template-columns: 86px minmax(0, 1fr); gap: 8px 12px; margin-top: 12px; }}
    .candidate-info-label {{ color: var(--muted); font-size: 13px; }}
    .candidate-chart-head {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 8px; }}
    .candidate-chart-title {{ font-weight: 700; color: var(--accent-2); }}
    .kline-toggle {{ display: inline-flex; gap: 6px; }}
    .kline-toggle button {{
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--surface);
      color: var(--muted);
      padding: 3px 10px;
      font-size: 13px;
      cursor: pointer;
    }}
    .kline-toggle button.active {{ background: var(--accent-soft); color: var(--accent); border-color: #b9dddd; font-weight: 700; }}
    .kline-pane {{ display: none; }}
    .kline-pane.active {{ display: flex; flex-direction: column; flex: 1; min-height: 0; }}
    .candidate-card .kline-chart {{ flex: 1; height: auto; min-height: 300px; margin: 8px 0 4px; }}
    .candidate-card .chart-note {{ margin-top: 4px; line-height: 1.35; }}
    .trend-block .candidate-chart-panel {{ border: 0; background: transparent; padding: 0; min-height: 0; }}
    .trend-block .candidate-chart-head {{ margin: 8px 0 6px; }}
    .trend-block .kline-pane.active {{ display: block; }}
    .review-field {{ display: grid; grid-template-columns: 74px minmax(0, 1fr); gap: 8px; margin: 7px 0; }}
    .review-field > span:first-child {{ color: var(--muted); font-size: 13px; }}
    .theme-block .review-field {{ grid-template-columns: 96px minmax(0, 1fr); gap: 14px; margin: 0; align-items: start; line-height: 2.0; }}
    .theme-block .review-field > span:first-child {{ font-size: 17px; padding-top: 6px; font-weight: 650; color: var(--accent-2); }}
    .theme-block .tag-list {{ gap: 10px; }}
    .theme-block .pill {{ font-size: 17px; padding: 6px 13px; line-height: 1.45; }}
    .theme-block .muted {{ font-size: 17px; line-height: 2.0; }}
    .tag-list {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .bucket-nav {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }}
    .bucket-link {{
      display: inline-flex;
      gap: 6px;
      align-items: center;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 4px 9px;
      background: var(--surface-soft);
      color: var(--text);
      font-size: 13px;
    }}
    .bucket-link span {{ color: var(--accent); font-weight: 700; }}
    .bucket-link:hover {{ border-color: var(--accent); background: var(--accent-soft); text-decoration: none; }}
    .bucket-counts {{ display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 6px; }}
    .event-meta {{ display: flex; flex-wrap: wrap; gap: 7px; margin: 8px 0; }}
    .pill, .badge {{
      display: inline-flex;
      align-items: center;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 2px 8px;
      background: var(--surface-soft);
      font-size: 13px;
      color: var(--muted);
      max-width: 100%;
    }}
    .badge {{ background: var(--accent-soft); color: var(--accent); border-color: #b9dddd; }}
    .detail-grid {{
      display: grid;
      grid-template-columns: 168px minmax(0, 1fr);
      gap: 7px 12px;
      margin-top: 10px;
    }}
    .detail-label {{ color: var(--muted); }}
    table {{ width: 100%; border-collapse: collapse; background: var(--surface); }}
    th, td {{ border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #eef3f7; }}
    ul {{ padding-left: 20px; }}
    li {{ margin: 6px 0; }}
    .warning {{
      border-left: 4px solid var(--bad);
      background: var(--bad-soft);
      color: #4a1616;
      padding: 12px 14px;
      margin: 12px 0;
      border-radius: 7px;
    }}
    .disclaimer {{
      border-left: 4px solid var(--warn);
      background: var(--warn-soft);
      padding: 12px 14px;
      color: #3a2a13;
      border-radius: 7px;
    }}
    pre {{
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      box-shadow: var(--shadow);
    }}
    pre code {{
      display: block;
      padding: 0;
      border: 0;
      background: transparent;
      font-size: 13px;
    }}
    .markdown-body {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      box-shadow: var(--shadow);
      overflow-wrap: anywhere;
    }}
    .markdown-body h1 {{ margin: 0 0 14px; font-size: 26px; }}
    .markdown-body h2 {{ margin-top: 22px; padding-top: 10px; border-top: 1px solid var(--line); }}
    .markdown-body h3 {{ margin-top: 16px; color: var(--accent-2); }}
    .markdown-body table {{ margin: 12px 0 16px; font-size: 14px; }}
    .markdown-body pre {{ box-shadow: none; background: var(--surface-soft); }}
    .markdown-body ul, .markdown-body ol {{ padding-left: 24px; }}
    @media (max-width: 900px) {{
      :root {{ --sidebar-width: 0px; --main-width: min(100vw - 20px, 1240px); --content-left: 10px; }}
      .side-nav {{ display: none; }}
      main {{ margin-left: 10px; margin-right: 10px; }}
      .brand-row, .page-hero, .console-grid, .review-card-head, .bucket-title-row {{ display: block; }}
      .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .review-card-grid, .review-sections, .review-subgrid, .candidate-card-layout {{ grid-template-columns: 1fr; }}
      .score-box {{ display: inline-block; margin-top: 8px; }}
      .bucket-counts {{ justify-content: flex-start; margin-top: 8px; }}
      .page-actions {{ justify-content: flex-start; margin-top: 12px; }}
    }}
    @media (max-width: 560px) {{
      main {{ width: min(100% - 20px, 1240px); }}
      .grid {{ grid-template-columns: 1fr; }}
      .detail-grid {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 21px; }}
      h2 {{ font-size: 19px; }}
    }}
  </style>
</head>
<body>
  <aside class="side-nav" aria-label="主导航">
    <div class="side-nav-panel">
      <div class="side-brand">
        <p class="side-brand-title">AStockFastLane</p>
        <p class="side-brand-subtitle">本地 A 股公开信息研究控制台</p>
      </div>
      <div class="side-tab">导航</div>
      <p class="side-nav-title">页面导航</p>
      <nav class="toolbar">
        <a class="button" href="/">首页</a>
        <a class="button" href="/daily-report">盘后报告</a>
        <a class="button" href="/candidate-review">候选审核池</a>
        <a class="button" href="/candidate-watchlist">热点候选池</a>
        <a class="button" href="/trend-analysis">短期趋势分析</a>
        <a class="button" href="/hot-events">热点分析</a>
        <a class="button" href="/hot-events-report">热点报告</a>
        <a class="button" href="/fast-report">Fast Report</a>
      </nav>
      <div class="side-footer">只读研究辅助<br>不自动写入 watchlist</div>
    </div>
  </aside>
  <main>{body}</main>
  <script>
    function toggleKlinePeriod(button) {{
      const chartId = button.getAttribute('data-chart-id');
      const period = button.getAttribute('data-period');
      const root = document.getElementById(chartId);
      if (!root) return;
      root.querySelectorAll('.kline-toggle button').forEach((item) => {{
        item.classList.toggle('active', item === button);
      }});
      root.querySelectorAll('.kline-pane').forEach((pane) => {{
        pane.classList.toggle('active', pane.getAttribute('data-period') === period);
      }});
    }}
  </script>
</body>
</html>"""
    return page.encode("utf-8")


def render_health_warnings(errors: list[str]) -> str:
    missing = [relative_path(path) for path in HEALTH_CHECK_PATHS if not path.exists()]
    warnings = missing + errors
    if not warnings:
        return '<section class="panel"><h2>数据健康与更新时间</h2><p class="muted">核心本地文件齐备，未发现读取错误。</p></section>'
    rows = "".join(f"<li>{esc(warning)}</li>" for warning in warnings)
    return f'<section class="warning"><strong>数据健康 warning</strong><ul>{rows}</ul></section>'


def is_time_label(label: Any) -> bool:
    text = text_value(label).lower()
    return any(token in text for token in ("time", "date", "created_at", "generated_at", "updated_at", "时间"))


def is_path_like(value: Any) -> bool:
    text = text_value(value)
    return "/" in text and any(text.endswith(suffix) for suffix in (".json", ".md", ".txt"))


def render_stat_cards(cards: list[tuple[str, Any] | tuple[str, Any, str]]) -> str:
    html_parts = []
    for card in cards:
        label, value = card[0], card[1]
        kind = card[2] if len(card) > 2 else ""
        if kind == "time" or (not kind and is_time_label(label)):
            display = format_datetime(value)
            value_class = "stat stat-time"
        elif kind == "path" or (not kind and is_path_like(value)):
            display = text_value(value) or "-"
            value_class = "stat stat-path"
        elif kind == "text":
            display = text_value(value) or "-"
            value_class = "stat stat-text"
        else:
            display = text_value(value) or "0"
            value_class = "stat"
        html_parts.append(
            f'<div class="summary-card"><div class="label">{esc(label)}</div><div class="{value_class}">{esc(display)}</div></div>'
        )
    return '<div class="grid">' + "".join(html_parts) + "</div>"


def render_candidate_overview(payload: dict[str, Any] | None, error: str | None) -> str:
    candidates = candidate_items(payload)
    in_count = sum(1 for item in candidates if item.get("in_watchlist") is True)
    out_count = len(candidates) - in_count
    warning = f'<div class="warning">warning: {esc(error)}</div>' if error else ""
    return f"""
<section>
  <h2>热点候选池概览</h2>
  {warning}
  {render_stat_cards([
        ("热点候选池数量", len(candidates)),
        ("生成时已命中长期 watchlist", in_count),
        ("生成时未命中长期 watchlist", out_count),
  ])}
  <div class="source-note">读取文件：<code>{esc(relative_path(CANDIDATE_WATCHLIST_JSON_PATH))}</code></div>
  <p class="muted">candidate_watchlist 是热点事件生成的候选池；watchlist 才是长期人工观察池。生成时 watchlist 标记仅代表候选文件生成时的历史标记。</p>
  <p><a href="/candidate-watchlist">打开热点候选池页面</a></p>
</section>"""


def render_candidate_kline_tabs(
    code: str,
    daily_k_index: dict[str, list[dict[str, Any]]] | None,
    weekly_k_index: dict[str, list[dict[str, Any]]] | None,
) -> str:
    chart_id = f"candidate-kline-{re.sub(r'[^0-9A-Za-z_-]', '-', code or 'unknown')}"
    daily_chart = render_kline_volume_chart((daily_k_index or {}).get(code, []), limit=20)
    weekly_bars = (weekly_k_index or {}).get(code, [])
    if weekly_bars:
        weekly_chart = render_kline_volume_chart(weekly_bars, limit=20)
    else:
        weekly_chart = '<div class="chart-empty">暂无周 K 数据。请先运行 <code>python scripts/probes/test_weekly_k_probe.py --limit 25 --weeks 80 --adjust-type qfq</code>。</div>'
    return f"""
<div class="candidate-chart-panel" id="{esc(chart_id)}">
  <div class="candidate-chart-head">
    <div class="candidate-chart-title">走势验证</div>
    <div class="kline-toggle" role="group" aria-label="K线周期切换">
      <button type="button" class="active" data-chart-id="{esc(chart_id)}" data-period="day" onclick="toggleKlinePeriod(this)">日K</button>
      <button type="button" data-chart-id="{esc(chart_id)}" data-period="week" onclick="toggleKlinePeriod(this)">周K</button>
    </div>
  </div>
  <div class="kline-pane active" data-period="day">{daily_chart}</div>
  <div class="kline-pane" data-period="week">{weekly_chart}</div>
</div>"""


def render_candidate_card(
    item: dict[str, Any],
    daily_k_index: dict[str, list[dict[str, Any]]] | None = None,
    weekly_k_index: dict[str, list[dict[str, Any]]] | None = None,
    include_chart: bool = True,
) -> str:
    code = text_value(item.get("code"))
    watchlist_label = "生成时已命中长期 watchlist" if item.get("in_watchlist") is True else "生成时未命中长期 watchlist"
    info_html = f"""
<div class="candidate-info-panel">
  <h3>{esc(code or "-")} {esc(item.get("name", "-"))}</h3>
  <div class="event-meta">
    <span class="pill">heat_score: {esc(item.get("heat_score", 0))}</span>
    <span class="pill">event_count: {esc(item.get("event_count", 0))}</span>
    <span class="pill">max_impact_strength: {esc(item.get("max_impact_strength", "-"))}</span>
    <span class="pill">生成时 watchlist 标记: {esc(watchlist_label)}</span>
  </div>
  <div class="candidate-info-grid">
    <div class="candidate-info-label">相关概念</div><div>{esc(ui_text(join_values(item.get("related_concepts"))))}</div>
    <div class="candidate-info-label">来源事件</div><div>{esc(ui_text(join_values(item.get("source_event_titles"))))}</div>
    <div class="candidate-info-label">候选角色</div><div>{esc(ui_text(join_values(item.get("roles"))))}</div>
    <div class="candidate-info-label">入选理由</div><div>{esc(ui_text(join_values(item.get("reasons"))))}</div>
    <div class="candidate-info-label">风险提示</div><div>{esc(ui_text(join_values(item.get("risk_notes"))))}</div>
    <div class="candidate-info-label">相关度</div><div>max {esc(item.get("relevance_score_max", 0))} / avg {esc(item.get("relevance_score_avg", 0))}</div>
    <div class="candidate-info-label">来源标签</div><div>{esc(item.get("label", "candidate_watchlist"))}</div>
  </div>
</div>"""
    if not include_chart:
        return f'<article class="event-card candidate-card">{info_html}</article>'
    chart_html = render_candidate_kline_tabs(code, daily_k_index, weekly_k_index)
    return f"""
<article class="event-card candidate-card">
  <div class="candidate-card-layout">
    {info_html}
    {chart_html}
  </div>
</article>"""


def render_candidate_watchlist(payload: dict[str, Any] | None, error: str | None, compact: bool = False) -> str:
    if not payload:
        return f'<section><h2>热点候选池</h2><div class="warning">warning: {esc(error or "暂无热点候选池输出。")}</div></section>'
    candidates = candidate_items(payload)
    daily_k_payload, daily_k_error = read_json(DAILY_K_PATH)
    weekly_k_payload, weekly_k_error = read_json(WEEKLY_K_PATH)
    daily_k_index = build_daily_k_index(daily_k_payload)
    weekly_k_index = build_daily_k_index(weekly_k_payload)
    limit = 4 if compact else 999
    cards = "".join(
        render_candidate_card(
            item,
            daily_k_index=daily_k_index,
            weekly_k_index=weekly_k_index,
            include_chart=not compact,
        )
        for item in candidates[:limit]
    )
    if not cards:
        cards = '<div class="panel">暂无热点候选池条目。</div>'
    more = ""
    if compact and len(candidates) > limit:
        more = f'<p class="muted">还有 {len(candidates) - limit} 个热点候选，打开详情页查看。</p>'
    chart_warning = ""
    if not compact:
        warnings = []
        if daily_k_error:
            warnings.append(f"日 K 文件读取失败：{daily_k_error}")
        if weekly_k_error:
            warnings.append(f"周 K 文件读取失败：{weekly_k_error}")
        if warnings:
            chart_warning = '<div class="warning"><strong>K 线数据 warning</strong><ul>' + "".join(
                f"<li>{esc(item)}</li>" for item in warnings
            ) + "</ul></div>"
    return f"""
{render_candidate_overview(payload, error)}
<section>
  <h2>热点候选池列表</h2>
  {chart_warning}
  {cards}
  {more}
</section>"""


def render_event_card(event: dict[str, Any]) -> str:
    concepts = ", ".join(concept_names(event)) or "-"
    keywords = ", ".join(matched_keywords(event)) or "-"
    stocks = candidate_stock_rows(event)
    stock_html = "<br>".join(stocks) if stocks else "无热点候选池关联；字段：code / name / role / relevance_score / reason / risk_note"
    logic = join_values(event.get("impact_logic"))
    risks = join_values(event.get("risk_notes"))
    url = text_value(event.get("url")) or "-"
    url_html = f'<a href="{esc(url)}" target="_blank" rel="noreferrer">{esc(url)}</a>' if url.startswith("http") else esc(url)
    return f"""
<article class="event-card">
  <h3>{esc(event.get("title", "-"))}</h3>
  <div class="event-meta">
    <span class="pill">事件类型: {esc(event.get("evidence_type", "-"))}</span>
    <span class="pill">影响方向: {esc(event.get("impact_direction", "-"))}</span>
    <span class="pill">影响强度: {esc(normalize_strength(event.get("impact_strength")))}</span>
    <span class="pill">analysis_level: {esc(event.get("analysis_level", "rule_based"))}</span>
  </div>
  <div class="detail-grid">
    <div class="detail-label">相关概念</div><div>{esc(concepts)}</div>
    <div class="detail-label">热点候选池关联</div><div>{stock_html}</div>
    <div class="detail-label">相关度</div><div>{esc("; ".join(text_value(s.get("relevance_score")) for s in event.get("related_stocks", []) if isinstance(s, dict) and text_value(s.get("relevance_score"))) or "-")}</div>
    <div class="detail-label">matched_keywords</div><div>{esc(keywords)}</div>
    <div class="detail-label">impact_logic</div><div>{esc(ui_text(logic))}</div>
    <div class="detail-label">risk_notes</div><div>{esc(ui_text(risks))}</div>
    <div class="detail-label">reason</div><div>{esc(ui_text(event.get("reason", "-")))}</div>
    <div class="detail-label">URL</div><div>{url_html}</div>
  </div>
</article>"""


def render_review_concept_note() -> str:
    return """
<section class="panel">
  <h2>candidate_review 说明</h2>
  <p><strong>watchlist</strong> 是长期人工观察池；<strong>candidate_watchlist</strong> 是热点候选池；<strong>candidate_review</strong> 是按用户偏好二次筛选后的候选审核池。</p>
  <p>本页只读展示 candidate_review，不会自动写入 watchlist，也不提供同步入口。</p>
  <p>人工审核状态来自 data/manual/candidate_review_status.json，仅只读展示。</p>
</section>"""


def render_key_takeaways(daily_payload: dict[str, Any] | None, review_payload: dict[str, Any] | None, hot_payload: dict[str, Any] | None) -> str:
    meta = daily_report_meta(daily_payload)
    status_summary = daily_payload.get("manual_status_summary", {}) if daily_payload else {}
    if not isinstance(status_summary, dict):
        status_summary = {}
    selected_count = len(daily_report_list(daily_payload, "selected_candidates")) if daily_payload else len(selected_review_items(candidate_review_items(review_payload)))
    hot_count = len(daily_report_list(daily_payload, "hot_mainlines")) if daily_payload else len(hot_events(hot_payload))
    return f"""
<section>
  <h2>今日关键结论</h2>
  {render_stat_cards([
        ("盘后报告时间", meta.get("created_at", "-"), "time"),
        ("热点主线", hot_count),
        ("候选审核重点", selected_count),
        ("待人工确认", status_summary.get("pending", selected_count)),
  ])}
  <p class="muted">首页只保留 30 秒浏览所需摘要。详细字段请进入盘后报告、候选审核池、热点候选池或短期趋势分析页面查看。</p>
</section>"""


def render_home_hot_mainlines(daily_payload: dict[str, Any] | None, hot_payload: dict[str, Any] | None) -> str:
    rows = daily_report_list(daily_payload, "hot_mainlines")[:5]
    cards = ""
    if rows:
        for item in rows:
            cards += f"""
<article class="event-card">
  <h3>{esc(item.get("title", "-"))}</h3>
  <div class="event-meta">
    <span class="pill">impact_strength: {esc(item.get("impact_strength", "-"))}</span>
    <span class="pill">impact_score: {esc(item.get("impact_score", "-"))}</span>
  </div>
</article>"""
    else:
        events = hot_events(hot_payload)[:5]
        cards = "".join(render_event_card(event) for event in events)
    if not cards:
        cards = '<div class="panel">暂无热点主线。</div>'
    return f"<section><h2>今日热点主线</h2>{cards}</section>"


def render_data_health_summary(errors: list[str], payloads: list[tuple[str, dict[str, Any] | None]]) -> str:
    rows = []
    for label, payload in payloads:
        meta = payload.get("meta", {}) if isinstance(payload, dict) else {}
        generated = payload.get("generated_at") if isinstance(payload, dict) else None
        created = meta.get("created_at") if isinstance(meta, dict) else None
        rows.append(f"<li>{esc(label)}: {esc(format_datetime(created or generated))}</li>")
    status = "存在 warning，请查看列表。" if errors else "核心页面读取正常。"
    warnings = ""
    if errors:
        warnings = "<ul>" + "".join(f"<li>{esc(error)}</li>" for error in errors) + "</ul>"
    return f"""
<section class="panel">
  <h2>数据健康与更新时间</h2>
  <p class="muted">{esc(status)}</p>
  <ul>{''.join(rows)}</ul>
  {warnings}
</section>"""


def render_home() -> bytes:
    hot_payload, hot_error = read_json(HOT_EVENTS_JSON_PATH)
    candidate_payload, candidate_error = read_json(CANDIDATE_WATCHLIST_JSON_PATH)
    candidate_review_payload, candidate_review_error = read_json(CANDIDATE_REVIEW_JSON_PATH)
    candidate_review_status_payload, candidate_review_status_error = read_json(CANDIDATE_REVIEW_STATUS_PATH)
    trend_payload, trend_error = read_json(TREND_ANALYSIS_JSON_PATH)
    daily_report_payload, daily_report_error = read_json(DAILY_AFTER_CLOSE_JSON_PATH)
    errors = [
        error
        for error in (
            hot_error,
            candidate_error,
            candidate_review_error,
            candidate_review_status_error,
            trend_error,
            daily_report_error,
        )
        if error
    ]
    review_items = candidate_review_items(candidate_review_payload)
    body = f"""
{render_page_header(
    "研究控制台",
    "盘后 30 秒浏览入口：先看关键结论，再进入对应只读页面展开。",
    "data/analysis/*_latest.json + reports/*_latest.md",
    actions=[("盘后报告", "/daily-report"), ("候选审核池", "/candidate-review"), ("热点候选池", "/candidate-watchlist")],
)}
{render_key_takeaways(daily_report_payload, candidate_review_payload, hot_payload)}
{render_daily_report(daily_report_payload, daily_report_error, compact=True)}
{render_candidate_review_selected(review_items, compact=True, status_index=build_review_status_index(candidate_review_status_payload))}
{render_home_hot_mainlines(daily_report_payload, hot_payload)}
{render_data_health_summary(errors, [
    ("盘后报告", daily_report_payload),
    ("候选审核池", candidate_review_payload),
    ("热点候选池", candidate_payload),
    ("短期趋势", trend_payload),
    ("热点分析", hot_payload),
])}
<section>
  <h2>免责声明</h2>
  <p class="disclaimer">{esc(DISCLAIMER)}</p>
</section>
"""
    return render_page("研究控制台", body)


def render_hot_events_page() -> bytes:
    hot_payload, hot_error = read_json(HOT_EVENTS_JSON_PATH)
    body = render_page_header(
        "热点分析",
        "按 impact_strength 分组查看本地热点事件和相关概念，只读展示。",
        relative_path(HOT_EVENTS_JSON_PATH),
        actions=[("Markdown 报告", "/hot-events-report")],
    )
    body += render_health_warnings([hot_error] if hot_error else [])
    body += render_hot_events(hot_payload, hot_error, compact=False)
    body += f'<section><h2>免责声明</h2><p class="disclaimer">{esc(DISCLAIMER)}</p></section>'
    return render_page("热点分析", body)


def render_candidate_watchlist_page() -> bytes:
    payload, error = read_json(CANDIDATE_WATCHLIST_JSON_PATH)
    body = render_page_header(
        "热点候选池",
        "candidate_watchlist 是由热点事件聚合生成的候选池，不是长期人工 watchlist。",
        relative_path(CANDIDATE_WATCHLIST_JSON_PATH),
    )
    body += render_health_warnings([error] if error else [])
    body += render_candidate_watchlist(payload, error, compact=False)
    body += f'<section><h2>免责声明</h2><p class="disclaimer">{esc(DISCLAIMER)}</p></section>'
    return render_page("热点候选池", body)


def render_candidate_review_page() -> bytes:
    payload, error = read_json(CANDIDATE_REVIEW_JSON_PATH)
    status_payload, status_error = read_json(CANDIDATE_REVIEW_STATUS_PATH)
    body = render_page_header(
        "候选审核池",
        "candidate_review 是按用户偏好二次筛选后的人工审核池，人工状态只读融合展示。",
        f"{relative_path(CANDIDATE_REVIEW_JSON_PATH)} + {relative_path(CANDIDATE_REVIEW_STATUS_PATH)}",
        actions=[("Markdown 报告", "/candidate-review-report")],
    )
    body += render_health_warnings([item for item in (error, status_error) if item])
    body += render_candidate_review(payload, error, compact=False, status_payload=status_payload)
    return render_page("候选审核池", body)


def render_trend_analysis_page() -> bytes:
    payload, error = read_json(TREND_ANALYSIS_JSON_PATH)
    body = render_page_header(
        "短期趋势分析",
        "展示本地趋势分析结果、趋势状态和风险备注，只读展示。",
        relative_path(TREND_ANALYSIS_JSON_PATH),
        actions=[("Markdown 报告", "/trend-analysis-report")],
    )
    body += render_health_warnings([error] if error else [])
    body += render_trend_analysis(payload, error, compact=False)
    body += f'<section><h2>免责声明</h2><p class="disclaimer">{esc(DISCLAIMER)}</p></section>'
    return render_page("短期趋势分析", body)


def render_daily_report_page() -> bytes:
    payload, error = read_json(DAILY_AFTER_CLOSE_JSON_PATH)
    body = render_page_header(
        "盘后报告",
        "整合热点主线、候选审核、人工状态和风险提示的本地盘后研究报告。",
        relative_path(DAILY_AFTER_CLOSE_JSON_PATH),
        actions=[("Markdown 报告", "/daily-report-report")],
    )
    body += render_health_warnings([error] if error else [])
    body += render_daily_report(payload, error, compact=False)
    return render_page("盘后报告", body)


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "AStockFastLaneDashboard/0.2"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path == "/":
            self.send_html(render_home())
        elif path == "/hot-events":
            self.send_html(render_hot_events_page())
        elif path in {"/hot-events-report", "/hot-events.md"}:
            self.send_html(render_markdown_page(HOT_EVENTS_MD_PATH, "热点事件报告"))
        elif path == "/candidate-watchlist":
            self.send_html(render_candidate_watchlist_page())
        elif path in {"/candidate-watchlist-report", "/candidate-watchlist.md"}:
            self.send_html(render_markdown_page(CANDIDATE_WATCHLIST_MD_PATH, "热点候选池报告"))
        elif path == "/candidate-review":
            self.send_html(render_candidate_review_page())
        elif path in {"/candidate-review-report", "/candidate-review.md"}:
            self.send_html(render_markdown_page(CANDIDATE_REVIEW_MD_PATH, "候选审核池报告"))
        elif path == "/daily-report":
            self.send_html(render_daily_report_page())
        elif path in {"/daily-report-report", "/daily-report.md"}:
            self.send_html(render_markdown_page(DAILY_AFTER_CLOSE_MD_PATH, "盘后报告"))
        elif path == "/trend-analysis":
            self.send_html(render_trend_analysis_page())
        elif path in {"/trend-analysis-report", "/trend-analysis.md"}:
            self.send_html(render_markdown_page(TREND_ANALYSIS_MD_PATH, "短期趋势分析报告"))
        elif path == "/fast-report":
            self.send_html(render_markdown_page(FAST_REPORT_PATH, "Fast Report"))
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Not found".encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def send_html(self, body: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local AStockFastLane web dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    url = f"http://{args.host}:{args.port}"
    print("AStockFastLane dashboard")
    print(f"Serving: {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
