# CNInfo Watchlist Announcement Probe Notes

## Scope

- Reads enabled symbols from `config/watchlist.json`.
- Fetches CNInfo announcement metadata only.
- Does not download or parse PDF files.
- Does not call an LLM or generate investment advice.

## Latest Verification

- Checked time: 2026-06-19T01:56:39.230720+08:00
- Watchlist path: config/watchlist.json
- Enabled stock count: 1
- Announcement item count: 10
- Failed stock count: 0

## Output Metadata

Each normalized item includes `query_code`, `query_name`, `query_market`, and `query_orgId` so downstream steps can trace which watchlist entry produced the announcement.
