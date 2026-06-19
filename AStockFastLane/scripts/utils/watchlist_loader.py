from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WATCHLIST_PATH = PROJECT_ROOT / "config" / "watchlist.json"


class WatchlistError(ValueError):
    """Raised when the watchlist configuration is missing or invalid."""


def infer_market(code: str) -> str:
    if code.startswith("6"):
        return "SH"
    if code.startswith(("0", "3")):
        return "SZ"
    if code.startswith(("8", "4")):
        return "BJ"
    return "UNKNOWN"


def validate_watchlist_item(item: Any, index: int) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        raise WatchlistError(f"items[{index}] must be an object")

    enabled = item.get("enabled", True)
    if not isinstance(enabled, bool):
        raise WatchlistError(f"items[{index}].enabled must be true or false")
    if not enabled:
        return None

    code = item.get("code")
    if not isinstance(code, str) or not code:
        raise WatchlistError(f"items[{index}].code is required and must be a string")
    code = code.strip()
    if not (len(code) == 6 and code.isdigit()):
        raise WatchlistError(f"items[{index}].code must be a 6-digit string, got: {code!r}")

    name = item.get("name")
    if not isinstance(name, str) or not name.strip():
        raise WatchlistError(f"items[{index}].name is required and must be a non-empty string")

    raw_market = item.get("market")
    if isinstance(raw_market, str) and raw_market.strip():
        market = raw_market.strip().upper()
    elif raw_market is None or raw_market == "":
        market = infer_market(code)
    else:
        raise WatchlistError(f"items[{index}].market must be a string when provided")

    note = item.get("note", "")
    if note is None:
        note = ""
    if not isinstance(note, str):
        raise WatchlistError(f"items[{index}].note must be a string when provided")

    return {
        "code": code,
        "name": name.strip(),
        "market": market,
        "enabled": True,
        "note": note.strip(),
    }


def load_watchlist(path: str | Path | None = None) -> list[dict[str, Any]]:
    watchlist_path = Path(path) if path is not None else DEFAULT_WATCHLIST_PATH
    try:
        payload = json.loads(watchlist_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WatchlistError(f"watchlist file not found: {watchlist_path}") from exc
    except json.JSONDecodeError as exc:
        raise WatchlistError(f"watchlist JSON decode failed: {exc}") from exc
    except OSError as exc:
        raise WatchlistError(f"watchlist read failed: {exc}") from exc

    if not isinstance(payload, dict):
        raise WatchlistError("watchlist root must be an object")

    items = payload.get("items")
    if not isinstance(items, list):
        raise WatchlistError("watchlist.items must be a list")

    enabled_items: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        normalized = validate_watchlist_item(item, index)
        if normalized is not None:
            enabled_items.append(normalized)
    return enabled_items
