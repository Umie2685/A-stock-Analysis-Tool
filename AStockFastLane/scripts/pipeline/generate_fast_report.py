from __future__ import annotations

import json
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_ROOT / "data" / "evidence" / "fast_evidence_pack_latest.json"
LATEST_OUTPUT_PATH = PROJECT_ROOT / "reports" / "fast_report_latest.md"
REPORT_TITLE = "AStockFastLane 快报"
DISCLAIMER = "本报告仅用于数据整理、信息归档和研究辅助，不构成任何投资建议、交易建议，也不承诺任何收益。"
LOCAL_TZ = timezone(timedelta(hours=8))


def now_local() -> datetime:
    return datetime.now(LOCAL_TZ)


def read_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [f"Input file not found: {path.relative_to(PROJECT_ROOT).as_posix()}"]
    except json.JSONDecodeError as exc:
        return None, [f"JSON decode failed: {exc}"]
    except OSError as exc:
        return None, [f"Input read failed: {exc}"]

    if not isinstance(payload, dict):
        return None, ["Input JSON root is not an object"]
    return payload, []


def md_text(value: Any, fallback: str = "-") -> str:
    if value is None:
        return fallback
    if isinstance(value, list):
        text = ", ".join(str(item).strip() for item in value if str(item).strip())
    else:
        text = str(value).strip()
    if not text:
        return fallback
    return text.replace("\r\n", "\n").replace("\r", "\n")


def first_text(item: dict[str, Any], keys: list[str], fallback: str = "-") -> str:
    for key in keys:
        value = item.get(key)
        text = md_text(value, "")
        if text:
            return text
    return fallback


def raw_ref(item: dict[str, Any]) -> dict[str, Any]:
    ref = item.get("raw_ref")
    return ref if isinstance(ref, dict) else {}


def raw_payload(item: dict[str, Any]) -> dict[str, Any]:
    raw = raw_ref(item).get("raw")
    return raw if isinstance(raw, dict) else {}


def first_nested_text(
    item: dict[str, Any],
    item_keys: list[str],
    ref_keys: list[str] | None = None,
    raw_keys: list[str] | None = None,
    fallback: str = "-",
) -> str:
    candidates = [
        first_text(item, item_keys, ""),
        first_text(raw_ref(item), ref_keys or [], ""),
        first_text(raw_payload(item), raw_keys or [], ""),
    ]
    for candidate in candidates:
        if candidate:
            return candidate
    return fallback


def normalize_type(value: Any) -> str:
    text = md_text(value, "").lower().replace("-", "_").replace(" ", "_")
    if text in {"news", "eastmoney_news"}:
        return "news"
    if text in {"announcement", "announcements", "cninfo_announcement"}:
        return "announcement"
    if text in {"research_report", "report", "reports", "eastmoney_report"}:
        return "research_report"
    return text


def get_type(item: dict[str, Any]) -> str:
    for key in ("evidence_type", "category", "type", "source_type", "source"):
        kind = normalize_type(item.get(key))
        if kind in {"news", "announcement", "research_report"}:
            return kind
    return ""


def collect_from_group(pack: dict[str, Any], keys: list[str]) -> list[dict[str, Any]]:
    for key in keys:
        value = pack.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def get_evidence_items(pack: dict[str, Any], errors: list[str]) -> list[dict[str, Any]]:
    if pack.get("success") is not True:
        errors.append("Fast Evidence Pack success is not true")

    pack_errors = pack.get("errors")
    if isinstance(pack_errors, list):
        errors.extend(str(error) for error in pack_errors if str(error).strip())

    grouped_items: list[dict[str, Any]] = []
    for group_keys in (
        ["news_items", "news", "news_evidence"],
        ["announcement_items", "announcements", "announcement_evidence"],
        ["research_report_items", "report_items", "reports", "research_reports", "research_report_evidence"],
    ):
        grouped_items.extend(collect_from_group(pack, group_keys))
    if grouped_items:
        return grouped_items

    items = pack.get("evidence_items", [])
    if not isinstance(items, list):
        errors.append("Fast Evidence Pack evidence_items is not a list")
        return []

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            normalized.append(item)
        else:
            errors.append(f"Skipped non-object evidence item at index {index}")
    return normalized


def split_items(
    items: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    news_items: list[dict[str, Any]] = []
    announcement_items: list[dict[str, Any]] = []
    report_items: list[dict[str, Any]] = []

    for item in items:
        kind = get_type(item)
        if kind == "news":
            news_items.append(item)
        elif kind == "announcement":
            announcement_items.append(item)
        elif kind == "research_report":
            report_items.append(item)

    return news_items, announcement_items, report_items


def list_value(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if isinstance(value, list) and value:
        return ", ".join(str(entry) for entry in value)
    return md_text(value, "-")


def render_news_items(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return ["暂无新闻证据。", ""]

    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        title = first_nested_text(item, ["title"], ["title"], ["title"], "未命名新闻")
        source = first_nested_text(item, ["source"], ["source"], [], "-")
        publish_time = first_nested_text(item, ["publish_time", "date"], ["publish_time", "date"], ["showTime"], "-")
        summary = first_nested_text(item, ["summary", "content"], ["summary", "content"], ["summary", "announcementContent"], "-")
        url = first_nested_text(item, ["url"], ["url"], [], "-")
        evidence_id = first_text(item, ["evidence_id"], f"news_{index:03d}")

        lines.extend(
            [
                f"### {index}. {title}",
                "",
                f"- 来源：{source}",
                f"- 发布时间：{publish_time}",
                f"- 摘要 / 内容片段：{summary}",
                f"- URL：{url}",
                f"- Evidence ID：`{evidence_id}`",
                "",
            ]
        )
    return lines


def stock_identity(item: dict[str, Any]) -> tuple[str, str, str]:
    raw = raw_payload(item)
    code = first_nested_text(
        item,
        ["query_code", "stock_code", "symbol", "code"],
        ["query_code", "stock_code", "symbol", "code"],
        ["stockCode", "secCode", "code"],
        "",
    )
    name = first_nested_text(
        item,
        ["query_name", "stock_name", "company", "name"],
        ["query_name", "stock_name", "company", "name"],
        ["stockName", "secName", "tileSecName", "name"],
        "",
    )
    market = first_nested_text(
        item,
        ["query_market", "market"],
        ["query_market", "market"],
        ["market"],
        "",
    )
    if not code:
        related = list_value(item, "related_symbols")
        code = "" if related == "-" else related
    if not name:
        name = first_text(raw, ["orgSName", "orgName"], "")
    return code or "-", name or "-", market or "-"


def stock_group_key(item: dict[str, Any]) -> tuple[str, str, str]:
    return stock_identity(item)


def format_stock_heading(index: int, key: tuple[str, str, str]) -> str:
    code, name, market = key
    parts = [part for part in (code, name, market) if part and part != "-"]
    heading = " ".join(parts) if parts else "未识别股票"
    return f"### 4.{index} {heading}"


def group_stock_items(
    announcement_items: list[dict[str, Any]], report_items: list[dict[str, Any]]
) -> "OrderedDict[tuple[str, str, str], dict[str, list[dict[str, Any]]]]":
    grouped: "OrderedDict[tuple[str, str, str], dict[str, list[dict[str, Any]]]]" = OrderedDict()

    for kind, items in (("announcements", announcement_items), ("reports", report_items)):
        for item in items:
            key = stock_group_key(item)
            if key not in grouped:
                grouped[key] = {"announcements": [], "reports": []}
            grouped[key][kind].append(item)

    return grouped


def render_announcement_items(items: list[dict[str, Any]], heading_level: int = 3) -> list[str]:
    if not items:
        return ["暂无公告证据。", ""]

    prefix = "#" * heading_level
    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        raw = raw_payload(item)
        title = first_nested_text(item, ["title"], ["title"], ["announcementTitle", "shortTitle"], "未命名公告")
        code, name, _market = stock_identity(item)
        publish_time = first_nested_text(
            item,
            ["publish_time", "announcement_date", "date"],
            ["publish_time", "announcement_date", "date"],
            ["announcementTime"],
            "-",
        )
        announcement_type = first_nested_text(
            item,
            ["announcement_type"],
            ["announcement_type"],
            ["announcementTypeName", "announcementType"],
            "-",
        )
        url = first_nested_text(item, ["url", "adjunctUrl"], ["url", "adjunctUrl"], ["url", "adjunctUrl"], "-")
        adjunct_url = first_nested_text(item, ["adjunctUrl"], ["adjunctUrl"], ["adjunctUrl"], "")
        evidence_id = first_text(item, ["evidence_id"], f"announcement_{index:03d}")

        lines.extend(
            [
                f"{prefix} {index}. {title}",
                "",
                f"- 股票代码：{code}",
                f"- 股票名称：{name}",
                f"- 公告时间 / 日期：{publish_time}",
                f"- 公告类型：{announcement_type}",
                f"- URL：{url}",
            ]
        )
        if adjunct_url:
            lines.append(f"- adjunctUrl：{adjunct_url}")
        if raw.get("announcementId"):
            lines.append(f"- announcementId：{md_text(raw.get('announcementId'))}")
        lines.extend([f"- Evidence ID：`{evidence_id}`", ""])
    return lines


def render_report_items(items: list[dict[str, Any]], heading_level: int = 3) -> list[str]:
    if not items:
        return ["暂无研报证据。", ""]

    prefix = "#" * heading_level
    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        title = first_nested_text(item, ["title"], ["title"], ["title"], "未命名研报")
        code, name, _market = stock_identity(item)
        institution = first_nested_text(item, ["institution"], ["institution"], ["orgSName", "orgName"], "-")
        analyst = first_nested_text(item, ["analyst"], ["analyst"], ["researcher", "author"], "-")
        publish_time = first_nested_text(item, ["publish_time", "date"], ["publish_time", "date"], ["publishDate"], "-")
        rating = first_nested_text(item, ["rating"], ["rating"], ["emRatingName", "sRatingName"], "-")
        target_price = first_nested_text(
            item,
            ["target_price", "targetPrice", "target_price_text"],
            ["target_price", "targetPrice", "target_price_text"],
            ["targetPrice", "targetPriceMin", "targetPriceMax"],
            "-",
        )
        url = first_nested_text(item, ["url"], ["url"], [], "-")
        evidence_id = first_text(item, ["evidence_id"], f"research_report_{index:03d}")

        lines.extend(
            [
                f"{prefix} {index}. {title}",
                "",
                f"- 股票代码：{code}",
                f"- 股票名称：{name}",
                f"- 机构名称：{institution}",
                f"- 分析师：{analyst}",
                f"- 发布时间 / 日期：{publish_time}",
                f"- rating / 机构评级（原始字段）：{rating}",
                f"- target_price / 目标价（原始字段）：{target_price}",
                f"- URL：{url}",
                f"- Evidence ID：`{evidence_id}`",
                "",
            ]
        )
    return lines


def render_watchlist_stock_evidence(
    announcement_items: list[dict[str, Any]], report_items: list[dict[str, Any]]
) -> list[str]:
    grouped = group_stock_items(announcement_items, report_items)
    if not grouped:
        return ["暂无观察池个股证据。", ""]

    lines: list[str] = []
    for index, (key, bucket) in enumerate(grouped.items(), start=1):
        lines.extend([format_stock_heading(index, key), ""])
        lines.extend(["#### 公告证据", ""])
        lines.extend(render_announcement_items(bucket["announcements"], heading_level=5))
        lines.extend(["#### 研报证据", ""])
        lines.extend(render_report_items(bucket["reports"], heading_level=5))
    return lines


def metadata_lines(pack: dict[str, Any] | None) -> list[str]:
    if not pack:
        return ["- generated_at：-", "- trade_date：-", "- date：-"]
    return [
        f"- generated_at：{md_text(pack.get('generated_at'), '-')}",
        f"- trade_date：{md_text(pack.get('trade_date'), '-')}",
        f"- date：{md_text(pack.get('date'), '-')}",
    ]


def build_report() -> tuple[str, int, int, int, int, bool, list[str]]:
    generated_at = now_local().isoformat()
    pack, errors = read_json(INPUT_PATH)
    sources: list[str] = []
    items: list[dict[str, Any]] = []

    if pack is not None:
        raw_sources = pack.get("sources", [])
        if isinstance(raw_sources, list):
            sources = [str(source) for source in raw_sources]
        items = get_evidence_items(pack, errors)

    news_items, announcement_items, report_items = split_items(items)
    success = bool(items) and not errors
    source_text = ", ".join(sources) if sources else "-"

    lines = [
        f"# {REPORT_TITLE}",
        "",
        "## 1. 报告说明",
        "",
        "本报告基于本地 Fast Evidence Pack 生成，仅对公开信息做结构化整理和归档，供研究辅助使用，不构成投资建议。",
        "",
        "## 2. 证据概览",
        "",
        f"- 报告生成时间：{generated_at}",
        f"- 输入文件：{INPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}",
        f"- 数据来源：{source_text}",
        f"- news 数量：{len(news_items)}",
        f"- announcement 数量：{len(announcement_items)}",
        f"- research_report 数量：{len(report_items)}",
        f"- total 数量：{len(items)}",
    ]
    lines.extend(metadata_lines(pack))
    lines.append("")

    if errors:
        lines.extend(["数据质量提示：", ""])
        lines.extend(f"- {error}" for error in errors)
        lines.append("")

    lines.extend(["## 3. 新闻证据", ""])
    lines.extend(render_news_items(news_items))
    lines.extend(["## 4. 观察池个股证据", ""])
    lines.extend(render_watchlist_stock_evidence(announcement_items, report_items))
    lines.extend(
        [
            "## 5. 免责声明",
            "",
            DISCLAIMER,
            "",
            "补充说明：公告部分仅展示元数据，不下载或解析 PDF；研报部分仅展示机构原始元数据，rating / target_price / 机构观点字段不代表本项目观点。",
            "",
        ]
    )

    return "\n".join(lines), len(items), len(news_items), len(announcement_items), len(report_items), success, errors


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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


def upsert_endpoint_results(
    item_count: int,
    news_count: int,
    announcement_count: int,
    report_count: int,
    success: bool,
    dated_output_path: Path,
    errors: list[str],
) -> None:
    doc_path = PROJECT_ROOT / "docs" / "endpoint_probe_results.md"
    existing = doc_path.read_text(encoding="utf-8") if doc_path.exists() else "# Endpoint Probe Results\n"
    marker = "## MVP2-005G Watchlist Grouped Markdown Report"

    status = "Success" if success else "Failed"
    lines = [
        marker,
        "",
        f"Status: {status}",
        "",
        f"Report input: {INPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}",
        "",
        "Output files:",
        "",
        f"- {dated_output_path.relative_to(PROJECT_ROOT).as_posix()}",
        f"- {LATEST_OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}",
        "",
        f"News item count: {news_count}",
        f"Announcement item count: {announcement_count}",
        f"Research report item count: {report_count}",
        f"Total evidence item count: {item_count}",
        "",
        "Notes:",
        "",
        "- Markdown report keeps news as a global section.",
        "- Announcement and research_report evidence are grouped under the watchlist stock evidence section.",
        "- Grouping prefers query_code / query_name / query_market and falls back to stock_code / stock_name / symbol / company.",
        "- Report generation reads Fast Evidence Pack only.",
        "- No network request, probe rerun, PDF download, LLM call, or third-party dependency was used by this report step.",
        "- Research report ratings and target prices are displayed as source metadata only.",
    ]

    if errors:
        lines.extend(["", "Errors:", ""])
        lines.extend(f"- {error}" for error in errors)

    doc_path.write_text(upsert_markdown_section(existing, marker, lines), encoding="utf-8")


def upsert_current_progress(success: bool, errors: list[str]) -> None:
    doc_path = PROJECT_ROOT / "docs" / "current_progress.md"
    existing = doc_path.read_text(encoding="utf-8") if doc_path.exists() else "# Current Progress\n"
    marker = "## MVP2-005G"
    status = "Completed" if success else "Failed"

    lines = [
        marker,
        "",
        f"Status: {status}",
        "",
        "Summary:",
        "",
        "- Upgraded Markdown report generation with a watchlist stock evidence section.",
        "- News evidence remains global.",
        "- Announcement and research_report evidence are grouped by query_code / query_name / query_market with stock field fallbacks.",
        "- Research report rating and target_price fields are displayed only as original source metadata.",
        "- No PDF download, LLM call, third-party dependency, or investment advice generation was added.",
        "",
        "Next:",
        "",
        "- MVP2-006G: add a one-click MVP2 pipeline runner.",
    ]

    if errors:
        lines.extend(["", "Errors:", ""])
        lines.extend(f"- {error}" for error in errors)

    doc_path.write_text(upsert_markdown_section(existing, marker, lines), encoding="utf-8")


def main() -> int:
    report, item_count, news_count, announcement_count, report_count, success, errors = build_report()
    today = now_local().strftime("%Y%m%d")
    dated_output_path = PROJECT_ROOT / "reports" / f"fast_report_{today}.md"

    write_text(dated_output_path, report)
    write_text(LATEST_OUTPUT_PATH, report)
    upsert_endpoint_results(
        item_count,
        news_count,
        announcement_count,
        report_count,
        success,
        dated_output_path,
        errors,
    )
    upsert_current_progress(success, errors)

    print("Report: fast_report")
    print(f"Input: {INPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Success: {success}")
    print(f"News item count: {news_count}")
    print(f"Announcement item count: {announcement_count}")
    print(f"Research report item count: {report_count}")
    print(f"Total evidence item count: {item_count}")
    print(f"Latest output: {LATEST_OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Dated output: {dated_output_path.relative_to(PROJECT_ROOT).as_posix()}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"- {error}")

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
