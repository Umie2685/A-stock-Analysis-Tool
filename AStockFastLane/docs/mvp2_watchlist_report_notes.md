# MVP2 Watchlist Report Notes

Status: Completed

## Scope

MVP2 adds a watchlist-aware report layer:

- News evidence remains a global section.
- Announcement evidence is grouped by watchlist stock.
- Research report evidence is grouped by watchlist stock.
- Grouping prefers `query_code`, `query_name`, and `query_market`.
- Fallback fields include `stock_code`, `stock_name`, `symbol`, and `company`.

## Run Entries

Offline report-only entry:

```bash
python scripts/run_offline_report.py
```

MVP1 compatibility refresh entry:

```bash
python scripts/run_mvp1_pipeline.py
```

MVP2 recommended refresh entry:

```bash
python scripts/run_mvp2_pipeline.py
```

## Watchlist

The watchlist file is:

```text
config/watchlist.json
```

Supported fields:

- `code`: six-digit A-share symbol.
- `name`: stock name.
- `market`: optional market label such as `SH`, `SZ`, or `BJ`.
- `enabled`: whether to include the symbol.
- `orgId`: optional CNInfo organization id.
- `note`: optional note.

## Boundaries

- No announcement PDF download.
- No research report PDF download.
- No PDF parsing.
- No LLM call.
- No third-party dependency.
- No investment advice generation.
- Research report rating, target price, and institution opinion fields are displayed only as original source metadata.
