from __future__ import annotations

from pathlib import Path

from utils.watchlist_loader import DEFAULT_WATCHLIST_PATH, WatchlistError, load_watchlist


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    display_path = DEFAULT_WATCHLIST_PATH.relative_to(PROJECT_ROOT).as_posix()
    print(f"Watchlist path: {display_path}")

    try:
        items = load_watchlist(DEFAULT_WATCHLIST_PATH)
    except WatchlistError as exc:
        print(f"ERROR: {exc}")
        print("Success: False")
        return 1

    print(f"Enabled symbols: {len(items)}")
    for item in items:
        print(f"- {item['code']} {item['name']} {item['market']}")
    print("Success: True")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
