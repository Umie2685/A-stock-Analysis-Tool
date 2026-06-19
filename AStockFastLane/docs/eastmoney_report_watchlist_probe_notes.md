# Eastmoney Report Watchlist Probe Notes

## Scope

- Reads enabled symbols from `config/watchlist.json`.
- Fetches Eastmoney research report metadata only.
- Does not download report PDFs or parse full report text.
- Does not call an LLM or generate investment advice.
- Rating, target price, and institution opinion fields are retained only as source metadata.

## Latest Verification

- Checked time: 2026-06-19T01:56:39.496367+08:00
- Watchlist path: config/watchlist.json
- Enabled stock count: 1
- Report item count: 10
- Failed stock count: 0

## Output Metadata

Each normalized item includes `query_code`, `query_name`, and `query_market` so downstream steps can trace which watchlist entry produced the report metadata.
