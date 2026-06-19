from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from utils.io_utils import write_json, write_text  # noqa: E402


LOCAL_TZ = timezone(timedelta(hours=8))
DEFAULT_CANDIDATE_PATH = PROJECT_ROOT / "data" / "analysis" / "candidate_watchlist_latest.json"
DEFAULT_TREND_PATH = PROJECT_ROOT / "data" / "analysis" / "trend_analysis_latest.json"
DEFAULT_PREFERENCES_PATH = PROJECT_ROOT / "config" / "user_stock_preferences.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "analysis"
REPORT_DIR = PROJECT_ROOT / "reports"
LATEST_JSON_PATH = OUTPUT_DIR / "candidate_review_latest.json"
LATEST_MD_PATH = REPORT_DIR / "candidate_review_latest.md"
DEFAULT_REVIEW_LIMIT = 5
DISCLAIMER = "Rule-based candidate review for research assistance only. Not investment advice."
REVIEW_BUCKETS = (
    "core_watch",
    "elastic_watch",
    "trend_watch",
    "market_height_watch",
    "skip",
    "blocked",
    "unknown",
)
TREND_SCORES = {
    "strong_uptrend": 20,
    "recovering": 15,
    "sideways": 5,
    "weakening": -10,
    "overheated": 8,
    "unknown": -20,
}
STRONG_TREND_STATES = {"strong_uptrend", "recovering", "sideways"}
REVIEW_BUCKET_LABELS = {
    "core_watch": "核心观察",
    "elastic_watch": "弹性观察",
    "trend_watch": "趋势观察",
    "market_height_watch": "市场高度观察",
    "skip": "暂不纳入",
    "blocked": "明确排除",
    "unknown": "信息不足",
}
THEME_ALIASES = {
    "AI硬件": ["AI算力", "AI服务器", "算力", "光通信", "数据中心"],
    "半导体设备": ["半导体国产替代", "半导体", "设备材料"],
    "半导体材料": ["半导体国产替代", "半导体材料", "设备材料"],
    "半导体新材料": ["半导体国产替代", "半导体新材料", "设备材料"],
    "国产替代": ["半导体国产替代", "国产替代"],
    "先进封装": ["封测", "封装", "IC载板"],
    "PCB": ["PCB", "印制电路板", "覆铜板"],
    "光模块": ["光通信", "光模块"],
    "CPO": ["光通信", "CPO"],
    "高速铜缆": ["高速互连", "铜缆", "连接器"],
    "连接器": ["连接器", "中航光电"],
    "算力硬件": ["AI算力", "算力", "服务器", "数据中心"],
    "存储": ["存储", "服务器"],
    "服务器电源": ["服务器", "数据中心", "电源"],
    "液冷": ["液冷", "温控", "数据中心"],
    "稀土": ["有色金属", "稀土", "北方稀土"],
    "小金属": ["有色金属", "小金属", "钨", "钼", "锂", "钴", "镍"],
    "战略资源": ["有色金属", "战略资源", "资源品", "稀土"],
    "涨价逻辑": ["有色金属", "涨价", "价格波动", "金属涨价"],
    "卡脖子材料": ["半导体国产替代", "卡脖子", "稀土", "材料"],
    "先进制造上游": ["半导体国产替代", "有色金属", "材料", "设备"],
    "半导体上游材料": ["半导体国产替代", "半导体", "材料"],
    "高端化工材料": ["高端化工", "化工材料"],
    "化工产品": ["化工"],
    "医药": ["创新药", "医药", "新药", "临床"],
    "消费": ["消费电子", "消费", "手机", "可穿戴"],
    "食品饮料": ["食品饮料", "白酒"],
    "低空经济": ["低空经济", "eVTOL", "无人机", "飞行汽车"],
    "传媒游戏": ["传媒游戏", "游戏"],
    "传统老登股": ["传统老登股"],
    "纯概念炒作": ["纯概念炒作"],
}


def now_local() -> datetime:
    return datetime.now(LOCAL_TZ)


def relative_path(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


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


def unique_texts(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = text_value(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def read_json_object(path: Path, label: str, errors: list[str], *, required: bool = True) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        message = f"File not found: {relative_path(path)}"
        errors.append(message)
        return None
    except json.JSONDecodeError as exc:
        errors.append(f"JSON decode failed: {relative_path(path)}: {exc}")
        return None
    except OSError as exc:
        errors.append(f"Read failed: {relative_path(path)}: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{label} JSON root is not an object: {relative_path(path)}")
        return None
    if required and not payload:
        errors.append(f"{label} JSON is empty: {relative_path(path)}")
    return payload


def preference_defaults() -> dict[str, Any]:
    return {
        "preferred_themes_strong": [],
        "preferred_themes_watch": [],
        "neutral_or_disabled_themes": [],
        "blocked_or_downrank_themes": [],
        "hard_filters": {
            "exclude_bj_market": True,
            "exclude_st": True,
            "exclude_new_listing": False,
            "exclude_overheated": False,
        },
        "overheated_policy": {
            "mode": "keep_as_market_height",
            "label": "market_height_watch",
            "risk_note": "短线过热标的仅作为市场高度和情绪风向观察，需要标记高波动风险。",
        },
        "review_limits": {
            "daily_review_limit": DEFAULT_REVIEW_LIMIT,
            "initial_bucket_quota": {"core_midcap": 2, "elastic_sentiment": 2, "trend_reserve": 1},
        },
        "weights": {
            "hotspot_weight": 0.5,
            "trend_weight": 0.5,
            "preference_weight": 0.5,
            "risk_penalty_weight": 0.3,
        },
        "watchlist_sync": {"mode": "manual_confirm", "auto_sync_to_watchlist": False},
    }


def merge_preferences(raw: dict[str, Any] | None, errors: list[str]) -> dict[str, Any]:
    prefs = preference_defaults()
    if raw is None:
        errors.append("Preference file unavailable; using defaults for schema only.")
        return prefs
    for key in (
        "preferred_themes_strong",
        "preferred_themes_watch",
        "neutral_or_disabled_themes",
        "blocked_or_downrank_themes",
    ):
        if isinstance(raw.get(key), list):
            prefs[key] = list_texts(raw.get(key))
        else:
            errors.append(f"Preference field {key} missing or not a list; using default.")
    for key in ("hard_filters", "overheated_policy", "review_limits", "weights", "watchlist_sync"):
        value = raw.get(key)
        if isinstance(value, dict):
            prefs[key].update(value)
        else:
            errors.append(f"Preference field {key} missing or not an object; using default.")
    return prefs


def normalize_code(value: Any) -> str:
    raw = text_value(value)
    digits = "".join(ch for ch in raw if ch.isdigit())
    return digits.zfill(6) if 0 < len(digits) <= 6 else digits


def infer_market(code: str) -> str:
    if code.startswith(("600", "601", "603", "605", "688")):
        return "SH"
    if code.startswith(("000", "001", "002", "003", "300", "301")):
        return "SZ"
    if code.startswith(("8", "4", "9")) and len(code) == 6:
        return "BJ"
    return ""


def contains_st_marker(name: str) -> bool:
    normalized = name.upper().replace(" ", "")
    return normalized.startswith("ST") or normalized.startswith("*ST") or " ST" in normalized


def candidate_text(candidate: dict[str, Any]) -> str:
    fields = [
        candidate.get("code"),
        candidate.get("name"),
        candidate.get("related_concepts"),
        candidate.get("source_event_titles"),
        candidate.get("roles"),
        candidate.get("reasons"),
        candidate.get("risk_notes"),
    ]
    return " ".join(text_value(field) for field in fields if text_value(field))


def match_theme_group(themes: list[str], haystack: str) -> list[str]:
    matches: list[str] = []
    lower_haystack = haystack.lower()
    for theme in themes:
        probes = [theme] + THEME_ALIASES.get(theme, [])
        if any(probe and probe.lower() in lower_haystack for probe in probes):
            matches.append(theme)
    return unique_texts(matches)


def build_trend_index(trend_payload: dict[str, Any] | None, errors: list[str]) -> dict[str, dict[str, Any]]:
    items = trend_payload.get("items", []) if trend_payload else []
    if not isinstance(items, list):
        errors.append("Trend file field items is missing or not a list.")
        return {}
    index: dict[str, dict[str, Any]] = {}
    for item in items:
        if isinstance(item, dict):
            code = normalize_code(item.get("code"))
            if code:
                index[code] = item
    return index


def trend_score_for(state: str) -> int:
    return TREND_SCORES.get(state, TREND_SCORES["unknown"])


def data_quality_problem(trend_item: dict[str, Any] | None) -> bool:
    if not trend_item:
        return True
    quality = trend_item.get("data_quality")
    if isinstance(quality, dict):
        if text_value(quality.get("status")) not in {"", "ok"}:
            return True
        problems = quality.get("problems")
        return isinstance(problems, list) and bool(problems)
    return False


def style_hint(candidate: dict[str, Any]) -> str:
    roles = " ".join(list_texts(candidate.get("roles")))
    name = text_value(candidate.get("name"))
    text = f"{name} {roles}"
    if any(key in text for key in ("服务器", "设备", "光模块", "资源", "运营", "制造", "中军")):
        return "core_midcap"
    if any(key in text for key in ("小票", "情绪", "飞行器", "机器人", "新技术")):
        return "elastic_sentiment"
    return "trend_reserve"


def score_preference(
    matched_strong: list[str],
    matched_watch: list[str],
    matched_disabled: list[str],
    matched_blocked: list[str],
) -> int:
    score = 0
    if matched_strong:
        score += 20
    if matched_watch:
        score += 10
    if matched_disabled and not matched_strong and not matched_watch:
        score -= 5
    if matched_blocked:
        score -= 20
    return score


def build_item(
    candidate: dict[str, Any],
    trend_item: dict[str, Any] | None,
    prefs: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    code = normalize_code(candidate.get("code"))
    name = text_value(candidate.get("name"))
    market = text_value(trend_item.get("market") if trend_item else "") or infer_market(code)
    trend_state = text_value(trend_item.get("trend_state") if trend_item else "") or "unknown"
    raw_heat_score = to_float(candidate.get("heat_score"))
    haystack = candidate_text(candidate)

    matched_strong = match_theme_group(prefs["preferred_themes_strong"], haystack)
    matched_watch = match_theme_group(prefs["preferred_themes_watch"], haystack)
    matched_disabled = match_theme_group(prefs["neutral_or_disabled_themes"], haystack)
    matched_blocked = match_theme_group(prefs["blocked_or_downrank_themes"], haystack)
    preference_score = score_preference(matched_strong, matched_watch, matched_disabled, matched_blocked)
    trend_score = trend_score_for(trend_state)

    hard_filters = prefs["hard_filters"]
    filter_reasons: list[str] = []
    data_issues: list[str] = []
    risk_notes = list_texts(candidate.get("risk_notes"))
    risk_notes.extend(list_texts(trend_item.get("risk_notes") if trend_item else []))
    if market == "BJ" and hard_filters.get("exclude_bj_market", True):
        filter_reasons.append("hard_filter: BJ market excluded")
    if contains_st_marker(name) and hard_filters.get("exclude_st", True):
        filter_reasons.append("hard_filter: ST marker excluded")
    if trend_state == "overheated" and hard_filters.get("exclude_overheated", False):
        filter_reasons.append("hard_filter: overheated excluded")
    if not trend_item:
        data_issues.append("missing trend analysis row")

    risk_penalty = 0
    if matched_blocked:
        risk_penalty += 20
    if trend_state == "weakening":
        risk_penalty += 10
    if trend_state == "unknown":
        risk_penalty += 20
    if data_quality_problem(trend_item):
        risk_penalty += 20
    if filter_reasons:
        risk_penalty += 30

    weights = prefs["weights"]
    final_score = round(
        raw_heat_score * to_float(weights.get("hotspot_weight"), 0.5)
        + preference_score * to_float(weights.get("preference_weight"), 0.5)
        + trend_score * to_float(weights.get("trend_weight"), 0.5)
        - risk_penalty * to_float(weights.get("risk_penalty_weight"), 0.3),
        2,
    )

    bucket, bucket_reason = classify_bucket(
        raw_heat_score=raw_heat_score,
        trend_state=trend_state,
        matched_strong=matched_strong,
        matched_watch=matched_watch,
        matched_disabled=matched_disabled,
        matched_blocked=matched_blocked,
        filter_reasons=filter_reasons,
        final_score=final_score,
        candidate=candidate,
    )
    if bucket == "market_height_watch":
        risk_notes.append(text_value(prefs["overheated_policy"].get("risk_note")))

    return {
        "code": code,
        "name": name,
        "market": market,
        "review_bucket": bucket,
        "review_score": final_score,
        "final_score": final_score,
        "raw_heat_score": raw_heat_score,
        "preference_score": preference_score,
        "trend_score": trend_score,
        "risk_penalty": risk_penalty,
        "bucket_reason": bucket_reason,
        "filter_reason": "; ".join(filter_reasons + data_issues) if filter_reasons or data_issues else "",
        "matched_preferred_themes": matched_strong,
        "matched_watch_themes": matched_watch,
        "matched_blocked_themes": matched_blocked,
        "matched_disabled_themes": matched_disabled,
        "related_concepts": list_texts(candidate.get("related_concepts")),
        "source_event_titles": list_texts(candidate.get("source_event_titles")),
        "trend_state": trend_state,
        "trend_reason": text_value(trend_item.get("trend_reason") if trend_item else ""),
        "trend_metrics": trend_item.get("metrics", {}) if isinstance(trend_item, dict) else {},
        "risk_notes": unique_texts(risk_notes),
        "observation_notes": list_texts(trend_item.get("observation_notes") if trend_item else []),
        "candidate_reasons": list_texts(candidate.get("reasons")),
        "candidate_roles": list_texts(candidate.get("roles")),
        "in_watchlist": candidate.get("in_watchlist") is True,
        "manual_confirm_required": True,
        "label": "candidate_review",
        "method": "rule_based",
        "created_at": created_at,
    }


def classify_bucket(
    *,
    raw_heat_score: float,
    trend_state: str,
    matched_strong: list[str],
    matched_watch: list[str],
    matched_disabled: list[str],
    matched_blocked: list[str],
    filter_reasons: list[str],
    final_score: float,
    candidate: dict[str, Any],
) -> tuple[str, str]:
    if filter_reasons:
        return "blocked", "触发硬过滤或缺少必要输入，需要人工排除或补齐数据。"
    if trend_state == "unknown":
        return "unknown", "缺少可用趋势状态，先保留为信息不足。"
    if matched_blocked and not (matched_strong or matched_watch):
        return "blocked", "命中降权或排除主题，且没有强偏好或保留关注主题修正。"
    if trend_state == "overheated":
        return "market_height_watch", "趋势状态为 overheated，按市场高度和情绪风向观察处理。"
    if matched_strong and trend_state in STRONG_TREND_STATES and raw_heat_score >= 18:
        if style_hint(candidate) == "core_midcap":
            return "core_watch", "命中强偏好主题，热点分较高，趋势状态不差，且角色更接近核心或中军。"
        return "elastic_watch", "命中强偏好主题，热点分较高，适合先放入弹性审核。"
    if (matched_strong or matched_watch) and trend_state != "unknown" and raw_heat_score >= 15:
        return "elastic_watch", "命中强偏好或保留关注主题，热点弹性较强，风险字段需要同步审核。"
    if trend_state in {"strong_uptrend", "recovering"} and final_score > 0:
        return "trend_watch", "趋势状态较好，但偏好命中不足，适合趋势观察。"
    if matched_disabled and not matched_strong and not matched_watch:
        return "skip", "仅命中暂不偏好主题，当前不进入重点审核。"
    return "skip", "相关性或趋势条件不足，暂不进入重点审核。"


def is_disabled_only_item(item: dict[str, Any]) -> bool:
    """Return True when an item only matches disabled themes, with no preferred/watch correction."""
    return bool(item.get("matched_disabled_themes")) and not item.get("matched_preferred_themes") and not item.get("matched_watch_themes")


def apply_review_quota(items: list[dict[str, Any]], prefs: dict[str, Any], limit: int) -> None:
    quotas = prefs["review_limits"].get("initial_bucket_quota", {})
    core_limit = int(to_float(quotas.get("core_midcap"), 2))
    elastic_limit = int(to_float(quotas.get("elastic_sentiment"), 2))
    trend_limit = int(to_float(quotas.get("trend_reserve"), 1))
    selected = 0
    counts = {"core_watch": 0, "elastic_or_height": 0, "trend_watch": 0}

    for item in sorted(items, key=lambda row: -to_float(row.get("final_score"))):
        item["selected_for_review"] = False
        if is_disabled_only_item(item):
            item["selection_note"] = "disabled_only: kept in full review pool, excluded from selected review list"
            continue

        bucket = text_value(item.get("review_bucket"))
        allowed = False
        if bucket == "core_watch" and counts["core_watch"] < core_limit:
            counts["core_watch"] += 1
            allowed = True
        elif bucket in {"elastic_watch", "market_height_watch"} and counts["elastic_or_height"] < elastic_limit:
            counts["elastic_or_height"] += 1
            allowed = True
        elif bucket == "trend_watch" and counts["trend_watch"] < trend_limit:
            counts["trend_watch"] += 1
            allowed = True

        if allowed and selected < limit:
            item["selected_for_review"] = True
            item["selection_note"] = "selected_by_bucket_quota"
            selected += 1
        elif allowed:
            item["selection_note"] = "review_limit_reached"
        else:
            item["selection_note"] = "bucket_quota_not_selected"


def bucket_summary(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(text_value(item.get("review_bucket")) or "unknown" for item in items)
    return {bucket: counts.get(bucket, 0) for bucket in REVIEW_BUCKETS}


def build_payload(candidate_path: Path, trend_path: Path, preferences_path: Path, limit_override: int | None = None) -> tuple[dict[str, Any], bool]:
    errors: list[str] = []
    candidate_payload = read_json_object(candidate_path, "candidate_watchlist", errors)
    trend_payload = read_json_object(trend_path, "trend_analysis", errors)
    raw_preferences = read_json_object(preferences_path, "user_stock_preferences", errors)
    prefs = merge_preferences(raw_preferences, errors)

    if candidate_payload is None or trend_payload is None or raw_preferences is None:
        created_at = now_local().isoformat()
        return (
            {
                "meta": {
                    "label": "candidate_review",
                    "created_at": created_at,
                    "method": "rule_based",
                    "input_candidate_file": relative_path(candidate_path),
                    "input_trend_file": relative_path(trend_path),
                    "preference_file": relative_path(preferences_path),
                    "review_limit": limit_override or DEFAULT_REVIEW_LIMIT,
                    "item_count": 0,
                    "selected_count": 0,
                    "blocked_count": 0,
                    "skip_count": 0,
                    "watchlist_sync_mode": "manual_confirm",
                    "disclaimer": DISCLAIMER,
                },
                "items": [],
                "buckets": {bucket: 0 for bucket in REVIEW_BUCKETS},
                "errors": errors,
            },
            False,
        )

    candidates = candidate_payload.get("candidates", [])
    if not isinstance(candidates, list):
        errors.append("Candidate file field candidates is missing or not a list.")
        candidates = []
    trend_index = build_trend_index(trend_payload, errors)
    created_at = now_local().isoformat()
    review_limit = limit_override or int(to_float(prefs["review_limits"].get("daily_review_limit"), DEFAULT_REVIEW_LIMIT))
    review_limit = max(1, review_limit)

    items = [
        build_item(candidate, trend_index.get(normalize_code(candidate.get("code"))), prefs, created_at)
        for candidate in candidates
        if isinstance(candidate, dict)
    ]
    items.sort(
        key=lambda item: (
            bucket_rank(text_value(item.get("review_bucket"))),
            -to_float(item.get("final_score")),
            -to_float(item.get("raw_heat_score")),
            text_value(item.get("code")),
        )
    )
    apply_review_quota(items, prefs, review_limit)
    buckets = bucket_summary(items)
    selected_count = sum(1 for item in items if item.get("selected_for_review") is True)

    payload = {
        "meta": {
            "label": "candidate_review",
            "created_at": created_at,
            "method": "rule_based",
            "input_candidate_file": relative_path(candidate_path),
            "input_trend_file": relative_path(trend_path),
            "preference_file": relative_path(preferences_path),
            "review_limit": review_limit,
            "item_count": len(items),
            "selected_count": selected_count,
            "blocked_count": buckets["blocked"],
            "skip_count": buckets["skip"],
            "watchlist_sync_mode": text_value(prefs["watchlist_sync"].get("mode")) or "manual_confirm",
            "auto_sync_to_watchlist": prefs["watchlist_sync"].get("auto_sync_to_watchlist") is True,
            "disclaimer": DISCLAIMER,
        },
        "items": items,
        "buckets": buckets,
        "errors": errors,
    }
    return payload, True


def bucket_rank(bucket: str) -> int:
    order = {
        "core_watch": 0,
        "elastic_watch": 1,
        "market_height_watch": 2,
        "trend_watch": 3,
        "skip": 4,
        "blocked": 5,
        "unknown": 6,
    }
    return order.get(bucket, 99)


def md_escape(value: Any) -> str:
    return text_value(value).replace("|", "\\|")


def md_join(values: Any) -> str:
    texts = list_texts(values)
    return "、".join(texts) if texts else "-"


def render_markdown(payload: dict[str, Any]) -> str:
    meta = payload.get("meta", {})
    buckets = payload.get("buckets", {})
    items = payload.get("items", [])
    if not isinstance(items, list):
        items = []
    if not isinstance(buckets, dict):
        buckets = {}
    selected = [item for item in items if isinstance(item, dict) and item.get("selected_for_review") is True]

    lines = [
        "# MVP5 候选审核池报告",
        "",
        f"- 生成时间: {meta.get('created_at', '-')}",
        "- 方法: rule_based",
        f"- 同步模式: {meta.get('watchlist_sync_mode', 'manual_confirm')}",
        f"- 风险提示: {DISCLAIMER}",
        "",
        "## 审核池概览",
        "",
        "| 分层 | 数量 |",
        "|---|---:|",
    ]
    for bucket in REVIEW_BUCKETS:
        lines.append(f"| {bucket} / {REVIEW_BUCKET_LABELS[bucket]} | {buckets.get(bucket, 0)} |")

    lines.extend(
        [
            "",
            "## 重点审核名单",
            "",
            "| 股票 | 代码 | 分层 | 分数 | 趋势 | 偏好命中 | 核心理由 |",
            "|---|---:|---|---:|---|---|---|",
        ]
    )
    for item in selected:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(item.get("name")),
                    md_escape(item.get("code")),
                    md_escape(item.get("review_bucket")),
                    md_escape(item.get("final_score")),
                    md_escape(item.get("trend_state")),
                    md_escape(item.get("matched_preferred_themes") or item.get("matched_watch_themes")),
                    md_escape(item.get("bucket_reason")),
                ]
            )
            + " |"
        )
    if not selected:
        lines.append("| - | - | - | - | - | - | 暂无进入重点审核的候选。 |")

    for bucket in REVIEW_BUCKETS:
        lines.extend(["", f"## {REVIEW_BUCKET_LABELS[bucket]} {bucket}", ""])
        bucket_items = [item for item in items if isinstance(item, dict) and item.get("review_bucket") == bucket]
        if not bucket_items:
            lines.append("暂无。")
            continue
        for item in bucket_items:
            lines.extend(
                [
                    f"### {item.get('name', '-')} {item.get('code', '-')}",
                    "",
                    f"- final_score: {item.get('final_score', 0)}",
                    f"- selected_for_review: {item.get('selected_for_review')}",
                    f"- trend_state: {item.get('trend_state', '-')}",
                    f"- matched_preferred_themes: {md_join(item.get('matched_preferred_themes'))}",
                    f"- matched_watch_themes: {md_join(item.get('matched_watch_themes'))}",
                    f"- matched_disabled_themes: {md_join(item.get('matched_disabled_themes'))}",
                    f"- matched_blocked_themes: {md_join(item.get('matched_blocked_themes'))}",
                    f"- bucket_reason: {item.get('bucket_reason', '-')}",
                    f"- filter_reason: {item.get('filter_reason') or '-'}",
                    f"- risk_notes: {md_join(item.get('risk_notes'))}",
                    "",
                ]
            )

    errors = payload.get("errors", [])
    if isinstance(errors, list) and errors:
        lines.extend(["", "## 数据健康提示", ""])
        for error in errors:
            lines.append(f"- {error}")

    return "\n".join(lines)


def write_outputs(payload: dict[str, Any]) -> tuple[Path, Path, Path, Path]:
    today = now_local().strftime("%Y%m%d")
    dated_json_path = OUTPUT_DIR / f"candidate_review_{today}.json"
    dated_md_path = REPORT_DIR / f"candidate_review_{today}.md"
    write_json(LATEST_JSON_PATH, payload)
    write_json(dated_json_path, payload)
    markdown = render_markdown(payload)
    write_text(LATEST_MD_PATH, markdown)
    write_text(dated_md_path, markdown)
    return LATEST_JSON_PATH, dated_json_path, LATEST_MD_PATH, dated_md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build MVP5 candidate review pool from candidate, trend, and preference files.")
    parser.add_argument("--limit", type=int, default=None, help="Review display limit. Defaults to preferences review limit.")
    parser.add_argument("--candidate-file", default=str(DEFAULT_CANDIDATE_PATH), help="Candidate watchlist JSON path.")
    parser.add_argument("--trend-file", default=str(DEFAULT_TREND_PATH), help="Trend analysis JSON path.")
    parser.add_argument("--preferences", default=str(DEFAULT_PREFERENCES_PATH), help="User stock preferences JSON path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidate_path = resolve_path(args.candidate_file)
    trend_path = resolve_path(args.trend_file)
    preferences_path = resolve_path(args.preferences)
    payload, ok = build_payload(candidate_path, trend_path, preferences_path, args.limit)
    if not ok:
        print("Candidate review build failed.")
        for error in payload.get("errors", []):
            print(f"- {error}")
        return 1

    json_path, dated_json_path, md_path, dated_md_path = write_outputs(payload)
    meta = payload["meta"]
    print("Candidate review: candidate_review")
    print(f"Items: {meta['item_count']}")
    print(f"Selected: {meta['selected_count']}")
    print(f"Blocked: {meta['blocked_count']}")
    print(f"Skip: {meta['skip_count']}")
    print(f"Buckets: {payload.get('buckets', {})}")
    print(f"Sync mode: {meta['watchlist_sync_mode']}")
    print(f"Latest JSON: {relative_path(json_path)}")
    print(f"Dated JSON: {relative_path(dated_json_path)}")
    print(f"Latest Markdown: {relative_path(md_path)}")
    print(f"Dated Markdown: {relative_path(dated_md_path)}")
    errors = payload.get("errors", [])
    if isinstance(errors, list) and errors:
        print("Warnings:")
        for error in errors:
            print(f"- {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
