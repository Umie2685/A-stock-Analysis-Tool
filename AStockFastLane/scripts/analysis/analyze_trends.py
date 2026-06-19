from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from utils.io_utils import write_json, write_text  # noqa: E402


LOCAL_TZ = timezone(timedelta(hours=8))
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "market" / "daily_k_latest.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "analysis"
REPORT_DIR = PROJECT_ROOT / "reports"
LATEST_JSON_PATH = OUTPUT_DIR / "trend_analysis_latest.json"
LATEST_MD_PATH = REPORT_DIR / "trend_analysis_latest.md"
DISCLAIMER = "规则版趋势分析仅用于公开信息整理和研究辅助，不构成交易指令，不承诺任何回报。"
TREND_STATES = ("strong_uptrend", "recovering", "sideways", "weakening", "overheated", "unknown")


def now_local() -> datetime:
    return datetime.now(LOCAL_TZ)


def relative_path(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def text_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def list_texts(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [text_value(value) for value in values if text_value(value)]


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


def to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def round_or_none(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def pct_change(latest: float, base: float) -> float | None:
    if base == 0:
        return None
    return (latest / base - 1) * 100


def normalize_bars(raw_bars: Any) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(raw_bars, list):
        return [], ["bars is not a list"]

    bars: list[dict[str, Any]] = []
    warnings: list[str] = []
    for index, raw in enumerate(raw_bars):
        if not isinstance(raw, dict):
            warnings.append(f"bars[{index}] is not an object")
            continue
        bar = {
            "trade_date": text_value(raw.get("trade_date")),
            "open": to_float(raw.get("open")),
            "high": to_float(raw.get("high")),
            "low": to_float(raw.get("low")),
            "close": to_float(raw.get("close")),
            "volume": to_float(raw.get("volume")),
        }
        bars.append(bar)

    bars.sort(key=lambda item: item.get("trade_date") or "")
    return bars, warnings


def validate_bars(bars: list[dict[str, Any]], source_status: str) -> list[str]:
    problems: list[str] = []
    if source_status != "ok":
        problems.append(f"source_daily_k_status is {source_status}")
    if not bars:
        problems.append("bars is empty")
    if len(bars) < 20:
        problems.append(f"bars count {len(bars)} is less than 20")
    for offset, bar in enumerate(bars[-20:], start=max(len(bars) - 20, 0)):
        for field in ("close", "high", "low", "volume"):
            if bar.get(field) is None:
                problems.append(f"bars[{offset}].{field} is missing or invalid")
    if bars and bars[-1].get("volume") == 0:
        problems.append("latest_volume is 0")
    return problems


def compute_metrics(bars: list[dict[str, Any]]) -> dict[str, Any]:
    closes = [float(bar["close"]) for bar in bars]
    highs = [float(bar["high"]) for bar in bars]
    volumes = [float(bar["volume"]) for bar in bars]
    latest_close = closes[-1]
    latest_volume = volumes[-1]
    high_20d = max(highs[-20:])
    previous_5_volumes = volumes[-10:-5] if len(volumes) >= 10 else []
    previous_5_volume_avg = mean(previous_5_volumes) if previous_5_volumes else None

    return {
        "ma5": round_or_none(mean(closes[-5:])),
        "ma10": round_or_none(mean(closes[-10:])),
        "ma20": round_or_none(mean(closes[-20:])),
        "pct_chg_1d": round_or_none(pct_change(latest_close, closes[-2])),
        "pct_chg_5d": round_or_none(pct_change(latest_close, closes[-6])),
        "pct_chg_10d": round_or_none(pct_change(latest_close, closes[-11])),
        "volume_ratio_5d": round_or_none(latest_volume / previous_5_volume_avg if previous_5_volume_avg else None),
        "drawdown_from_20d_high": round_or_none(pct_change(latest_close, high_20d)),
        "distance_to_20d_high": round_or_none(pct_change(latest_close, high_20d)),
        "latest_close": round_or_none(latest_close),
        "latest_volume": round_or_none(latest_volume, 0),
        "latest_trade_date": text_value(bars[-1].get("trade_date")),
    }


def state_risk_notes(state: str) -> list[str]:
    mapping = {
        "overheated": ["短期涨幅较大，追高波动风险上升。", "规则版分析未包含基本面和公告风险。"],
        "strong_uptrend": ["趋势较强但可能受大盘、板块轮动和消息面影响。", "该结论不构成交易指令。"],
        "recovering": ["修复趋势可能失败，需要观察量能和均线延续性。"],
        "sideways": ["短期方向不明确，可能继续震荡。"],
        "weakening": ["短期走弱，需关注是否继续下破关键均线。"],
        "unknown": ["数据不足或数据质量不支持趋势判断。"],
    }
    return mapping.get(state, mapping["unknown"])


def observation_notes(state: str) -> list[str]:
    mapping = {
        "overheated": ["观察后续波动是否收敛，以及量能是否明显回落。"],
        "strong_uptrend": ["观察 MA5/MA10/MA20 排列是否延续，以及量能是否保持温和放大。"],
        "recovering": ["观察收盘价能否继续站稳短期均线，并逐步修复与 20 日高点的距离。"],
        "sideways": ["观察是否出现放量突破或跌破震荡区间。"],
        "weakening": ["观察是否重新站回 MA10/MA20，或继续扩大回撤。"],
        "unknown": ["先补齐或刷新日 K 数据，再进行规则判断。"],
    }
    return mapping.get(state, mapping["unknown"])


def evaluate_state(metrics: dict[str, Any]) -> tuple[str, list[str], int]:
    latest_close = metrics["latest_close"]
    ma5 = metrics["ma5"]
    ma10 = metrics["ma10"]
    ma20 = metrics["ma20"]
    pct_5d = metrics["pct_chg_5d"]
    pct_10d = metrics["pct_chg_10d"]
    volume_ratio = metrics["volume_ratio_5d"]
    drawdown = metrics["drawdown_from_20d_high"]

    if pct_5d is not None and volume_ratio is not None and drawdown is not None:
        if pct_5d >= 20 and drawdown > -3 and volume_ratio >= 1.8:
            return "overheated", ["pct_chg_5d >= 20", "distance_to_20d_high > -3", "volume_ratio_5d >= 1.8"], 85
    if pct_10d is not None and drawdown is not None:
        if pct_10d >= 30 and drawdown > -5:
            return "overheated", ["pct_chg_10d >= 30", "drawdown_from_20d_high > -5"], 82

    if (
        latest_close is not None
        and ma5 is not None
        and ma10 is not None
        and ma20 is not None
        and pct_5d is not None
        and volume_ratio is not None
        and latest_close > ma5 > ma10 > ma20
        and pct_5d > 5
        and volume_ratio >= 1.2
    ):
        return "strong_uptrend", ["close > ma5 > ma10 > ma20", "pct_chg_5d > 5", "volume_ratio_5d >= 1.2"], 78

    if latest_close is not None and ma5 is not None and ma10 is not None and pct_5d is not None and drawdown is not None:
        if latest_close > ma5 and (ma5 >= ma10 or pct_5d > 3) and drawdown <= -5:
            return "recovering", ["close > ma5", "ma5 >= ma10 or pct_chg_5d > 3", "drawdown_from_20d_high <= -5"], 62

    if latest_close is not None and ma10 is not None and ma20 is not None and pct_5d is not None:
        if latest_close < ma10 and pct_5d < -5:
            return "weakening", ["close < ma10", "pct_chg_5d < -5"], 35
        if latest_close < ma20:
            return "weakening", ["close < ma20"], 38

    return "sideways", ["data sufficient", "no stronger trend rule matched"], 50


def build_reason(name: str, state: str, metrics: dict[str, Any]) -> str:
    state_cn = {
        "strong_uptrend": "strong_uptrend",
        "recovering": "recovering",
        "sideways": "sideways",
        "weakening": "weakening",
        "overheated": "overheated",
        "unknown": "unknown",
    }[state]
    if state == "unknown":
        return f"{name} 的日 K 数据质量不足，规则判定为 {state_cn}。"
    return (
        f"最近收盘价为 {metrics.get('latest_close')}，MA5/MA10/MA20 分别为 "
        f"{metrics.get('ma5')}/{metrics.get('ma10')}/{metrics.get('ma20')}，"
        f"5 日涨跌幅为 {metrics.get('pct_chg_5d')}%，成交量较前 5 日均量为 "
        f"{metrics.get('volume_ratio_5d')} 倍，20 日高点距离为 "
        f"{metrics.get('distance_to_20d_high')}%，规则判定为 {state_cn}。"
    )


def unknown_item(item: dict[str, Any], problems: list[str], created_at: str, bars: list[dict[str, Any]]) -> dict[str, Any]:
    name = text_value(item.get("name"))
    metrics = {
        "ma5": None,
        "ma10": None,
        "ma20": None,
        "pct_chg_1d": None,
        "pct_chg_5d": None,
        "pct_chg_10d": None,
        "volume_ratio_5d": None,
        "drawdown_from_20d_high": None,
        "distance_to_20d_high": None,
        "latest_close": None,
        "latest_volume": None,
    }
    return {
        "code": text_value(item.get("code")),
        "name": name,
        "market": text_value(item.get("market")),
        "heat_score": item.get("heat_score"),
        "related_concepts": list_texts(item.get("related_concepts")),
        "trend_state": "unknown",
        "trend_score": 0,
        "trend_reason": build_reason(name or text_value(item.get("code")), "unknown", metrics),
        "trigger_conditions": problems,
        "risk_notes": state_risk_notes("unknown"),
        "observation_notes": observation_notes("unknown"),
        "data_quality": {"status": "unknown", "problems": problems, "bar_count": len(bars)},
        "metrics": metrics,
        "source_daily_k_status": text_value(item.get("data_status")) or "unknown",
        "latest_trade_date": text_value(bars[-1].get("trade_date")) if bars else "",
        "created_at": created_at,
        "label": "trend_analysis",
        "method": "rule_based",
    }


def analyze_item(item: dict[str, Any], created_at: str) -> dict[str, Any]:
    bars, bar_warnings = normalize_bars(item.get("bars"))
    source_status = text_value(item.get("data_status")) or "unknown"
    problems = validate_bars(bars, source_status)
    problems.extend(bar_warnings)
    if problems:
        return unknown_item(item, problems, created_at, bars)

    try:
        metrics = compute_metrics(bars)
        state, triggers, score = evaluate_state(metrics)
    except (ValueError, TypeError, ZeroDivisionError) as exc:
        return unknown_item(item, [f"metric calculation failed: {exc}"], created_at, bars)

    name = text_value(item.get("name"))
    return {
        "code": text_value(item.get("code")),
        "name": name,
        "market": text_value(item.get("market")),
        "heat_score": item.get("heat_score"),
        "related_concepts": list_texts(item.get("related_concepts")),
        "trend_state": state,
        "trend_score": score,
        "trend_reason": build_reason(name or text_value(item.get("code")), state, metrics),
        "trigger_conditions": triggers,
        "risk_notes": state_risk_notes(state),
        "observation_notes": observation_notes(state),
        "data_quality": {"status": "ok", "problems": [], "bar_count": len(bars)},
        "metrics": metrics,
        "source_daily_k_status": source_status,
        "latest_trade_date": metrics.get("latest_trade_date", ""),
        "created_at": created_at,
        "label": "trend_analysis",
        "method": "rule_based",
    }


def state_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    return {state: sum(1 for item in items if item.get("trend_state") == state) for state in TREND_STATES}


def build_payload(input_path: Path) -> dict[str, Any]:
    created_at = now_local().isoformat()
    payload, errors = read_json_object(input_path)
    source_items = payload.get("items", []) if payload else []
    if not isinstance(source_items, list):
        source_items = []
        errors.append("daily_k items is missing or not a list")
    items = [analyze_item(item, created_at) for item in source_items if isinstance(item, dict)]
    counts = state_counts(items)
    return {
        "meta": {
            "label": "trend_analysis",
            "created_at": created_at,
            "source_file": relative_path(input_path),
            "method": "rule_based",
            "item_count": len(items),
            "ok_count": len(items) - counts["unknown"],
            "unknown_count": counts["unknown"],
            "state_counts": counts,
            "disclaimer": DISCLAIMER,
        },
        "items": items,
        "errors": errors,
    }


def md_escape(value: Any) -> str:
    return text_value(value).replace("|", "\\|")


def render_markdown(payload: dict[str, Any]) -> str:
    meta = payload.get("meta", {})
    items = payload.get("items", [])
    if not isinstance(items, list):
        items = []
    counts = meta.get("state_counts", {})
    if not isinstance(counts, dict):
        counts = {}

    lines = [
        "# MVP4 短期趋势分析报告",
        "",
        f"- 生成时间：{meta.get('created_at', '-')}",
        f"- 数据来源：{meta.get('source_file', '-')}",
        "- 分析方法：rule_based",
        f"- 风险提示：{DISCLAIMER}",
        "",
        "## 概览",
        "",
        f"- 样本数量：{meta.get('item_count', 0)}",
        f"- 可分析数量：{meta.get('ok_count', 0)}",
        f"- unknown 数量：{meta.get('unknown_count', 0)}",
        f"- 状态统计：strong_uptrend={counts.get('strong_uptrend', 0)}，recovering={counts.get('recovering', 0)}，sideways={counts.get('sideways', 0)}，weakening={counts.get('weakening', 0)}，overheated={counts.get('overheated', 0)}，unknown={counts.get('unknown', 0)}",
        "",
        "| 股票 | 代码 | 热度 | 趋势状态 | 最新交易日 | 核心原因 |",
        "|---|---:|---:|---|---|---|",
    ]

    for item in items:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(item.get("name")),
                    md_escape(item.get("code")),
                    md_escape(item.get("heat_score")),
                    md_escape(item.get("trend_state")),
                    md_escape(item.get("latest_trade_date")),
                    md_escape(item.get("trend_reason")),
                ]
            )
            + " |"
        )

    lines.extend(["", "## 详细分析", ""])
    for item in items:
        metrics = item.get("metrics", {})
        if not isinstance(metrics, dict):
            metrics = {}
        lines.extend(
            [
                f"### {text_value(item.get('name')) or '-'} {text_value(item.get('code')) or '-'}",
                "",
                f"- 趋势状态：{text_value(item.get('trend_state'))}",
                f"- 规则原因：{text_value(item.get('trend_reason'))}",
                f"- 触发条件：{'；'.join(list_texts(item.get('trigger_conditions'))) or '-'}",
                (
                    "- 关键指标："
                    f"latest_close={metrics.get('latest_close')}，"
                    f"ma5={metrics.get('ma5')}，ma10={metrics.get('ma10')}，ma20={metrics.get('ma20')}，"
                    f"pct_chg_1d={metrics.get('pct_chg_1d')}%，pct_chg_5d={metrics.get('pct_chg_5d')}%，pct_chg_10d={metrics.get('pct_chg_10d')}%，"
                    f"volume_ratio_5d={metrics.get('volume_ratio_5d')}，"
                    f"distance_to_20d_high={metrics.get('distance_to_20d_high')}%"
                ),
                f"- 风险提示：{'；'.join(list_texts(item.get('risk_notes'))) or '-'}",
                f"- 观察条件：{'；'.join(list_texts(item.get('observation_notes'))) or '-'}",
                "",
            ]
        )

    errors = payload.get("errors", [])
    if isinstance(errors, list) and errors:
        lines.extend(["## 数据健康提示", ""])
        for error in errors:
            lines.append(f"- {error}")
        lines.append("")

    return "\n".join(lines)


def write_outputs(payload: dict[str, Any]) -> tuple[Path, Path, Path, Path]:
    today = now_local().strftime("%Y%m%d")
    dated_json_path = OUTPUT_DIR / f"trend_analysis_{today}.json"
    dated_md_path = REPORT_DIR / f"trend_analysis_{today}.md"
    write_json(LATEST_JSON_PATH, payload)
    write_json(dated_json_path, payload)
    md_text = render_markdown(payload)
    write_text(LATEST_MD_PATH, md_text)
    write_text(dated_md_path, md_text)
    return LATEST_JSON_PATH, dated_json_path, LATEST_MD_PATH, dated_md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze short-term trend states from daily K output.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT_PATH), help="Input daily K JSON path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path
    payload = build_payload(input_path)
    json_path, dated_json_path, md_path, dated_md_path = write_outputs(payload)
    meta = payload["meta"]
    print("Trend analysis: trend_analysis")
    print(f"Source: {meta['source_file']}")
    print(f"Items: {meta['item_count']}")
    print(f"OK: {meta['ok_count']}")
    print(f"Unknown: {meta['unknown_count']}")
    print(f"State counts: {meta['state_counts']}")
    print(f"Latest JSON: {relative_path(json_path)}")
    print(f"Dated JSON: {relative_path(dated_json_path)}")
    print(f"Latest Markdown: {relative_path(md_path)}")
    print(f"Dated Markdown: {relative_path(dated_md_path)}")
    errors = payload.get("errors", [])
    if isinstance(errors, list) and errors:
        print("Errors:")
        for error in errors:
            print(f"- {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
