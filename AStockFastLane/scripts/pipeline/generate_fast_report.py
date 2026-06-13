from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_ROOT / "data" / "evidence" / "fast_evidence_pack_latest.json"
LATEST_OUTPUT_PATH = PROJECT_ROOT / "reports" / "fast_report_latest.md"
REPORT_TITLE = "AStockFastLane Fast Report"
DISCLAIMER = "本报告仅用于数据整理和研究辅助，不构成投资建议。"
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


def md_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    return text.replace("\r\n", "\n").replace("\r", "\n")


def get_evidence_items(pack: dict[str, Any], errors: list[str]) -> list[dict[str, Any]]:
    if pack.get("success") is not True:
        errors.append("Fast Evidence Pack success is not true")

    pack_errors = pack.get("errors")
    if isinstance(pack_errors, list):
        errors.extend(str(error) for error in pack_errors)

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


def split_items(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    news_items = [item for item in items if item.get("category") == "news"]
    announcement_items = [item for item in items if item.get("category") == "announcement"]
    return news_items, announcement_items


def render_news_items(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return ["暂无新闻证据。", ""]

    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        title = md_text(item.get("title"), "未命名新闻")
        publish_time = md_text(item.get("publish_time"), "未知时间")
        source = md_text(item.get("source"), "未知来源")
        url = md_text(item.get("url"), "无链接")
        summary = md_text(item.get("summary"), "无摘要")
        evidence_id = md_text(item.get("evidence_id"), f"news_{index:03d}")

        lines.extend(
            [
                f"### {index}. {title}",
                "",
                f"- 发布时间：{publish_time}",
                f"- 来源：{source}",
                f"- URL：{url}",
                f"- 摘要：{summary}",
                f"- Evidence ID：`{evidence_id}`",
                "",
            ]
        )
    return lines


def render_announcement_items(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return ["暂无公告证据。", ""]

    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        title = md_text(item.get("title"), "未命名公告")
        publish_time = md_text(item.get("publish_time"), "未知时间")
        source = md_text(item.get("source"), "未知来源")
        url = md_text(item.get("url"), "无链接")
        evidence_id = md_text(item.get("evidence_id"), f"announcement_{index:03d}")
        related_symbols = item.get("related_symbols", [])
        if isinstance(related_symbols, list) and related_symbols:
            symbols_text = ", ".join(str(symbol) for symbol in related_symbols)
        else:
            symbols_text = "无"

        lines.extend(
            [
                f"### {index}. {title}",
                "",
                f"- 发布时间：{publish_time}",
                f"- 来源：{source}",
                f"- URL：{url}",
                f"- 相关代码：{symbols_text}",
                f"- Evidence ID：`{evidence_id}`",
                "",
            ]
        )
    return lines


def build_report() -> tuple[str, int, int, int, bool, list[str]]:
    generated_at = now_local().isoformat()
    pack, errors = read_json(INPUT_PATH)
    sources: list[str] = []
    items: list[dict[str, Any]] = []

    if pack is not None:
        raw_sources = pack.get("sources", [])
        if isinstance(raw_sources, list):
            sources = [str(source) for source in raw_sources]
        items = get_evidence_items(pack, errors)

    news_items, announcement_items = split_items(items)
    success = bool(items) and not errors
    source_text = ", ".join(sources) if sources else "未知"

    lines = [
        f"# {REPORT_TITLE}",
        "",
        f"生成时间：{generated_at}",
        f"数据来源：{source_text}",
        f"Evidence item 数量：{len(items)}",
        f"新闻证据数量：{len(news_items)}",
        f"公告证据数量：{len(announcement_items)}",
        "",
        "## 1. 摘要",
        "",
    ]

    if success:
        lines.extend(
            [
                (
                    f"本报告基于 Fast Evidence Pack 中的 {len(items)} 条证据生成，"
                    f"其中新闻 {len(news_items)} 条、公告 {len(announcement_items)} 条。"
                    "报告仅做公开信息整理和研究辅助，不输出投资结论。"
                ),
                "",
            ]
        )
    else:
        lines.extend(
            [
                "本次报告生成过程中发现输入数据不可用或存在错误，因此仅生成失败说明。",
                "",
                "错误信息：",
                "",
            ]
        )
        lines.extend(f"- {error}" for error in errors or ["未知错误"])
        lines.append("")

    lines.extend(["## 2. 新闻证据", ""])
    lines.extend(render_news_items(news_items))
    lines.extend(["## 3. 公告证据", ""])
    lines.extend(render_announcement_items(announcement_items))
    lines.extend(
        [
            "## 4. 数据质量说明",
            "",
            "- 数据来自本地 Fast Evidence Pack。",
            "- 新闻数据来自 Eastmoney news probe。",
            "- 公告数据来自 CNInfo announcement probe，当前只保存公告元数据，未下载 PDF。",
            "- 当前仍是 MVP 小样本流程，来源覆盖和字段稳定性需要后续继续验证。",
            "- endpoint 可能变化，后续应保留 raw/cache 以便追溯。",
            "- 本报告不调用 LLM，不做交易判断。",
            "",
            "## 5. 免责声明",
            "",
            DISCLAIMER,
            "",
        ]
    )

    return "\n".join(lines), len(items), len(news_items), len(announcement_items), success, errors


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def upsert_endpoint_results(
    item_count: int,
    news_count: int,
    announcement_count: int,
    success: bool,
    dated_output_path: Path,
    errors: list[str],
) -> None:
    doc_path = PROJECT_ROOT / "docs" / "endpoint_probe_results.md"
    existing = doc_path.read_text(encoding="utf-8") if doc_path.exists() else "# Endpoint Probe Results\n"
    marker = "## MVP0-009G+010G Markdown Report and Pipeline"
    before = existing.split(marker, 1)[0].rstrip()

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
        f"Total evidence item count: {item_count}",
        "",
        "Notes:",
        "",
        "- Markdown report supports news and announcement sections.",
        "- Report generation reads Fast Evidence Pack only.",
        "- No LLM call was made.",
        "- Report does not provide investment advice.",
    ]

    if errors:
        lines.extend(["", "Errors:", ""])
        lines.extend(f"- {error}" for error in errors)

    doc_path.write_text(f"{before}\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def upsert_current_progress(success: bool, errors: list[str]) -> None:
    doc_path = PROJECT_ROOT / "docs" / "current_progress.md"
    existing = doc_path.read_text(encoding="utf-8") if doc_path.exists() else "# Current Progress\n"
    marker = "## MVP0-009G+010G"
    before = existing.split(marker, 1)[0].rstrip()
    status = "Completed" if success else "Failed"

    lines = [
        marker,
        "",
        f"Status: {status}",
        "",
        "Summary:",
        "",
        "- Upgraded Markdown report for news + announcements.",
        "- Added one-click MVP0 pipeline runner.",
        "",
        "Next:",
        "",
        "- MVP0-011G: Prepare MVP0 release notes and README update.",
    ]

    if errors:
        lines.extend(["", "Errors:", ""])
        lines.extend(f"- {error}" for error in errors)

    doc_path.write_text(f"{before}\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report, item_count, news_count, announcement_count, success, errors = build_report()
    today = now_local().strftime("%Y%m%d")
    dated_output_path = PROJECT_ROOT / "reports" / f"fast_report_{today}.md"

    write_text(dated_output_path, report)
    write_text(LATEST_OUTPUT_PATH, report)
    upsert_endpoint_results(
        item_count,
        news_count,
        announcement_count,
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

