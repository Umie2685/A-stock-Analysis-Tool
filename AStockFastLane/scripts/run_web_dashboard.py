from __future__ import annotations

import argparse
import html
import json
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
FAST_REPORT_PATH = PROJECT_ROOT / "reports" / "fast_report_latest.md"
HEALTH_CHECK_PATHS = [
    HOT_EVENTS_JSON_PATH,
    HOT_EVENTS_MD_PATH,
    CANDIDATE_WATCHLIST_JSON_PATH,
    CANDIDATE_WATCHLIST_MD_PATH,
    EVIDENCE_PATH,
    FAST_REPORT_PATH,
]
STRENGTH_ORDER = ["high", "medium", "low", "unknown"]
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
            f"{esc(code)} / {esc(name)} / {esc(role)} / relevance_score {esc(score)} / "
            f"reason: {esc(reason)} / risk_note: {esc(risk_note)}"
        )
    return rows


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
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #667085;
      --line: #d7dce3;
      --accent: #176b87;
      --accent-soft: #e7f3f6;
      --warn: #8a4b12;
      --bad: #9f1d1d;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.55;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      background: #ffffff;
      padding: 20px 28px;
    }}
    main {{
      width: min(1180px, calc(100% - 32px));
      margin: 24px auto 48px;
    }}
    h1 {{ margin: 0 0 6px; font-size: 28px; letter-spacing: 0; }}
    h2 {{ margin: 28px 0 12px; font-size: 20px; letter-spacing: 0; }}
    h3 {{ margin: 18px 0 8px; font-size: 16px; letter-spacing: 0; }}
    p {{ margin: 8px 0; }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .muted {{ color: var(--muted); }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .stat {{ font-size: 30px; font-weight: 700; }}
    .label {{ color: var(--muted); font-size: 13px; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }}
    .button {{
      display: inline-block;
      border: 1px solid var(--accent);
      border-radius: 6px;
      padding: 7px 10px;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 14px;
    }}
    table {{ width: 100%; border-collapse: collapse; background: var(--panel); }}
    th, td {{ border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #edf1f5; }}
    ul {{ padding-left: 20px; }}
    li {{ margin: 7px 0; }}
    .event-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      margin: 12px 0;
    }}
    .event-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 8px 0;
    }}
    .pill {{
      display: inline-block;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 2px 8px;
      background: #f8fafc;
      font-size: 13px;
      color: var(--muted);
    }}
    .detail-grid {{
      display: grid;
      grid-template-columns: 140px minmax(0, 1fr);
      gap: 6px 10px;
      margin-top: 8px;
    }}
    .detail-label {{ color: var(--muted); }}
    .warning {{
      border-left: 4px solid var(--bad);
      background: #fff1f1;
      color: #471313;
      padding: 12px 14px;
      margin: 12px 0;
    }}
    .disclaimer {{
      border-left: 4px solid var(--warn);
      background: #fff8ee;
      padding: 12px 14px;
      color: #3b2a18;
    }}
    pre {{
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    @media (max-width: 820px) {{
      header {{ padding: 16px; }}
      main {{ width: min(100% - 20px, 1180px); margin-top: 16px; }}
      .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 520px) {{
      .grid {{ grid-template-columns: 1fr; }}
      .detail-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>AStockFastLane</h1>
    <p class="muted">本地 A 股公开信息研究辅助 Dashboard</p>
    <nav class="toolbar">
      <a class="button" href="/">首页</a>
      <a class="button" href="/hot-events">热点分析</a>
      <a class="button" href="/hot-events-report">热点报告</a>
      <a class="button" href="/candidate-watchlist">候选观察股</a>
      <a class="button" href="/fast-report">Fast Report</a>
    </nav>
  </header>
  <main>{body}</main>
</body>
</html>"""
    return page.encode("utf-8")


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


def render_health_warnings(errors: list[str]) -> str:
    missing = [relative_path(path) for path in HEALTH_CHECK_PATHS if not path.exists()]
    warnings = missing + errors
    if not warnings:
        return ""
    rows = "".join(f"<li>{esc(warning)}</li>" for warning in warnings)
    return f'<section class="warning"><strong>数据健康 warning</strong><ul>{rows}</ul></section>'


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
            f'<div class="muted">{esc(publish_time)}</div>'
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
            f"<li>{esc(first_text(item, ['title']) or '-')}<div class=\"muted\">{esc(first_text(item, ['publish_time', 'date']))}</div></li>"
            for item in bucket["announcements"][:5]
        ) or "<li>暂无公告证据。</li>"
        report_html = "".join(
            f"<li>{esc(first_text(item, ['title']) or '-')}<div class=\"muted\">{esc(first_text(item, ['publish_time', 'date']))}</div></li>"
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


def render_hot_overview(payload: dict[str, Any] | None, events: list[dict[str, Any]]) -> str:
    counts = strength_counts(events)
    concepts = payload.get("matched_concepts", []) if payload else []
    concept_text = "、".join(
        f"{item.get('concept', '-')}({item.get('event_count', 0)})"
        for item in concepts
        if isinstance(item, dict)
    ) or "-"
    candidate_count = text_value(payload.get("candidate_watchlist_count")) if payload else "0"
    stat_rows = [
        ("热点事件总数", len(events)),
        ("high", counts["high"]),
        ("medium", counts["medium"]),
        ("low", counts["low"]),
        ("unknown", counts["unknown"]),
        ("候选观察股数量", candidate_count or "0"),
    ]
    cards = "".join(
        f'<div class="panel"><div class="label">{esc(label)}</div><div class="stat">{esc(value)}</div></div>'
        for label, value in stat_rows
    )
    return f"""
<section>
  <h2>热点概览</h2>
  <div class="grid">{cards}</div>
  <p>命中概念列表：{esc(concept_text)}</p>
  <p>规则版分析说明：本页读取本地 hot_events_latest.json，按 impact_strength 分组展示；分析方式为 rule_based。</p>
  <p><a href="/hot-events-report">打开 hot_events_latest.md 报告预览</a></p>
</section>"""


def render_event_card(event: dict[str, Any]) -> str:
    concepts = ", ".join(concept_names(event)) or "-"
    keywords = ", ".join(matched_keywords(event)) or "-"
    stocks = candidate_stock_rows(event)
    stock_html = (
        "<br>".join(stocks)
        if stocks
        else "无候选观察股；字段：code / name / role / relevance_score / reason / risk_note"
    )
    logic = join_values(event.get("impact_logic"))
    risks = join_values(event.get("risk_notes"))
    url = text_value(event.get("url")) or "-"
    url_html = f'<a href="{esc(url)}" target="_blank" rel="noreferrer">{esc(url)}</a>' if url.startswith("http") else esc(url)
    return f"""
<article class="event-card">
  <h3>{esc(event.get("title", "-"))}</h3>
  <div class="event-meta">
    <span class="pill">事件类型：{esc(event.get("evidence_type", "-"))}</span>
    <span class="pill">影响方向：{esc(event.get("impact_direction", "-"))}</span>
    <span class="pill">影响力度：{esc(normalize_strength(event.get("impact_strength")))}</span>
    <span class="pill">analysis_level: {esc(event.get("analysis_level", "rule_based"))}</span>
  </div>
  <div class="detail-grid">
    <div class="detail-label">相关概念</div><div>{esc(concepts)}</div>
    <div class="detail-label">候选观察股</div><div>{stock_html}</div>
    <div class="detail-label">相关度</div><div>{esc("; ".join(text_value(s.get("relevance_score")) for s in event.get("related_stocks", []) if isinstance(s, dict) and text_value(s.get("relevance_score"))) or "-")}</div>
    <div class="detail-label">matched_keywords</div><div>{esc(keywords)}</div>
    <div class="detail-label">impact_logic</div><div>{esc(logic)}</div>
    <div class="detail-label">risk_notes</div><div>{esc(risks)}</div>
    <div class="detail-label">reason</div><div>{esc(event.get("reason", "-"))}</div>
    <div class="detail-label">URL</div><div>{url_html}</div>
  </div>
</article>"""


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


def render_candidate_overview(payload: dict[str, Any] | None, error: str | None) -> str:
    candidates = candidate_items(payload)
    in_count = sum(1 for item in candidates if item.get("in_watchlist") is True)
    out_count = len(candidates) - in_count
    cards = "".join(
        f'<div class="panel"><div class="label">{esc(label)}</div><div class="stat">{esc(value)}</div></div>'
        for label, value in [
            ("候选观察股数量", len(candidates)),
            ("已在 watchlist", in_count),
            ("未在 watchlist", out_count),
        ]
    )
    warning = f'<div class="warning">warning: {esc(error)}</div>' if error else ""
    return f"""
<section>
  <h2>候选观察股概览</h2>
  {warning}
  <div class="grid">{cards}</div>
  <p>候选观察股由本地 hot_events_latest.json 聚合生成，仅用于研究辅助。</p>
  <p><a href="/candidate-watchlist">打开候选观察股页面</a></p>
</section>"""


def render_candidate_card(item: dict[str, Any]) -> str:
    return f"""
<article class="event-card">
  <h3>{esc(item.get("code", "-"))} {esc(item.get("name", "-"))}</h3>
  <div class="event-meta">
    <span class="pill">heat_score: {esc(item.get("heat_score", 0))}</span>
    <span class="pill">event_count: {esc(item.get("event_count", 0))}</span>
    <span class="pill">max_impact_strength: {esc(item.get("max_impact_strength", "-"))}</span>
    <span class="pill">in_watchlist: {esc(item.get("in_watchlist", False))}</span>
  </div>
  <div class="detail-grid">
    <div class="detail-label">related_concepts</div><div>{esc(join_values(item.get("related_concepts")))}</div>
    <div class="detail-label">source_event_titles</div><div>{esc(join_values(item.get("source_event_titles")))}</div>
    <div class="detail-label">roles</div><div>{esc(join_values(item.get("roles")))}</div>
    <div class="detail-label">reasons</div><div>{esc(join_values(item.get("reasons")))}</div>
    <div class="detail-label">risk_notes</div><div>{esc(join_values(item.get("risk_notes")))}</div>
    <div class="detail-label">relevance_score</div><div>max {esc(item.get("relevance_score_max", 0))} / avg {esc(item.get("relevance_score_avg", 0))}</div>
    <div class="detail-label">label</div><div>{esc(item.get("label", "candidate_watchlist"))}</div>
  </div>
</article>"""


def render_candidate_watchlist(payload: dict[str, Any] | None, error: str | None, compact: bool = False) -> str:
    if not payload:
        return f'<section><h2>候选观察股</h2><div class="warning">warning: {esc(error or "暂无候选观察股输出。")}</div></section>'
    candidates = candidate_items(payload)
    limit = 5 if compact else 999
    cards = "".join(render_candidate_card(item) for item in candidates[:limit])
    if not cards:
        cards = '<div class="panel">暂无候选观察股。</div>'
    more = ""
    if compact and len(candidates) > limit:
        more = f'<p class="muted">还有 {len(candidates) - limit} 个候选观察股，打开详情页查看。</p>'
    return f"""
{render_candidate_overview(payload, error)}
<section>
  <h2>候选观察股列表</h2>
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


def render_home() -> bytes:
    watchlist_payload, watchlist_error = read_json(WATCHLIST_PATH)
    evidence_payload, evidence_error = read_json(EVIDENCE_PATH)
    hot_payload, hot_error = read_json(HOT_EVENTS_JSON_PATH)
    candidate_payload, candidate_error = read_json(CANDIDATE_WATCHLIST_JSON_PATH)
    report_text, report_error = read_text(FAST_REPORT_PATH, limit=5000)

    watchlist_items = enabled_watchlist_items(watchlist_payload)
    items = evidence_items(evidence_payload)
    news, announcements, reports = split_evidence(items)
    errors = [error for error in (watchlist_error, evidence_error, hot_error, candidate_error, report_error) if error]

    body = f"""
{render_health_warnings(errors)}
{render_stats(len(news), len(announcements), len(reports))}
{render_watchlist(watchlist_items, watchlist_error)}
{render_news(news)}
{render_stock_evidence(announcements, reports)}
{render_hot_events(hot_payload, hot_error, compact=True)}
{render_candidate_watchlist(candidate_payload, candidate_error, compact=True)}
{render_fast_report_summary(report_text, report_error)}
<section>
  <h2>免责声明</h2>
  <p class="disclaimer">{esc(DISCLAIMER)}</p>
</section>
"""
    return render_page("AStockFastLane Dashboard", body)


def render_hot_events_page() -> bytes:
    hot_payload, hot_error = read_json(HOT_EVENTS_JSON_PATH)
    body = render_health_warnings([hot_error] if hot_error else [])
    body += render_hot_events(hot_payload, hot_error, compact=False)
    body += f'<section><h2>免责声明</h2><p class="disclaimer">{esc(DISCLAIMER)}</p></section>'
    return render_page("热点事件分析", body)


def render_candidate_watchlist_page() -> bytes:
    payload, error = read_json(CANDIDATE_WATCHLIST_JSON_PATH)
    body = render_health_warnings([error] if error else [])
    body += render_candidate_watchlist(payload, error, compact=False)
    body += f'<section><h2>免责声明</h2><p class="disclaimer">{esc(DISCLAIMER)}</p></section>'
    return render_page("候选观察股", body)


def render_markdown_page(path: Path, title: str) -> bytes:
    text, error = read_text(path)
    if error:
        body = f'<section class="warning"><strong>数据健康 warning</strong><p>{esc(error)}</p></section>'
    else:
        body = f"<pre>{esc(text)}</pre>"
    return render_page(title, body)


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
            self.send_html(render_markdown_page(CANDIDATE_WATCHLIST_MD_PATH, "候选观察股报告"))
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
