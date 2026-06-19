# Fast Evidence Pack Watchlist Notes

## Scope

- Reads existing probe cache JSON only.
- Does not access the network or run probes.
- Does not download PDFs, call an LLM, or generate investment advice.
- Keeps news evidence independent from watchlist metadata for now.

## Watchlist Metadata

Announcement evidence items preserve these fields when available:

- `query_code`
- `query_name`
- `query_market`
- `query_orgId`
- `stock_code`
- `stock_name`

Research report evidence items preserve these fields when available:

- `query_code`
- `query_name`
- `query_market`
- `stock_code`
- `stock_name`

The existing `category` field remains unchanged. The builder also writes `evidence_type` with the same logical value for compatibility with later MVP2 steps.
