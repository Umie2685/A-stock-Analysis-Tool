# Endpoint Probe Results

No endpoint probe has been executed in MVP0-001.

## MVP0-003 Eastmoney News Probe

Status: Success

Checked time: 2026-06-19T01:56:38.953106+08:00

Endpoint: https://np-weblist.eastmoney.com/comm/web/getFastNewsList?client=web&biz=web_724&fastColumn=102&sortEnd=&pageSize=10&req_trace=astockfastlane-84f95dda5a8c47b29367543b6929b410

Request limit: 10 items, 1 request, timeout 10s

Output files:

- data/raw/eastmoney_news_probe_20260619.json
- data/cache/eastmoney_news_probe_latest.json

Observed fields:

- title
- publish_time
- source
- url
- summary
- raw

Notes:

- Parsed 10 item(s).
- Uses one Eastmoney global 7x24 fast-news endpoint only.
- No provider, pipeline, evidence pack, or report was generated.

## MVP2-002G CNInfo Watchlist Announcement Probe

Status: Success

Checked time: 2026-06-19T01:56:39.230720+08:00

Endpoint: https://www.cninfo.com.cn/new/hisAnnouncement/query

Method: POST

Watchlist path: config/watchlist.json
Enabled watchlist count: 1
Failed stock count: 0

Request limit: 10 items per enabled stock, timeout 15s

Output files:

- data/raw/cninfo_announcement_probe_20260619.json
- data/cache/cninfo_announcement_probe_latest.json

Observed fields:

- query_code
- query_name
- query_market
- title
- publish_time
- company
- symbol
- announcement_type
- url
- raw

Notes:

- Parsed 10 item(s).
- Reads enabled symbols from config/watchlist.json.
- Uses the CNInfo announcement endpoint only.
- Does not download or parse announcement PDFs.
- No provider, evidence pack, report, LLM, or investment advice logic was generated.

## MVP2-003G Eastmoney Report Watchlist Probe

Status: Success

Checked time: 2026-06-19T01:56:39.496367+08:00

Endpoint: https://reportapi.eastmoney.com/report/list

Method: GET

Watchlist path: config/watchlist.json
Enabled watchlist count: 1
Failed stock count: 0

Request limit: 10 items per enabled stock, timeout 15s

Output files:

- data/raw/eastmoney_report_probe_20260619.json
- data/cache/eastmoney_report_probe_latest.json

Observed fields:

- query_code
- query_name
- query_market
- title
- publish_time
- institution
- analyst
- company
- symbol
- rating
- url
- summary
- raw

Notes:

- Parsed 10 item(s).
- Reads enabled symbols from config/watchlist.json.
- Uses the Eastmoney reportapi endpoint only.
- Does not download report PDFs or parse full report text.
- Rating, target price, and institution opinion fields are stored only as source metadata.
- No evidence pack, report generation, LLM, or investment advice logic was changed.

## MVP1-002G Multi-source Fast Evidence Pack with Reports

Status: Success

Inputs:

- data/cache/eastmoney_news_probe_latest.json
- data/cache/cninfo_announcement_probe_latest.json
- data/cache/eastmoney_report_probe_latest.json

Output files:

- data/evidence/fast_evidence_pack_20260619.json
- data/evidence/fast_evidence_pack_latest.json

News item count: 10
Announcement item count: 10
Report item count: 10
Total evidence item count: 30

Notes:

- Built from cached Eastmoney news, CNInfo announcement, and Eastmoney report probe JSON only.
- No network request was made.
- No Markdown report was generated.
- CNInfo announcement records are metadata only; PDFs were not downloaded.
- Eastmoney report records are institution opinion metadata only; no investment conclusion was generated.

## MVP2-005G Watchlist Grouped Markdown Report

Status: Success

Report input: data/evidence/fast_evidence_pack_latest.json

Output files:

- reports/fast_report_20260619.md
- reports/fast_report_latest.md

News item count: 10
Announcement item count: 10
Research report item count: 10
Total evidence item count: 30

Notes:

- Markdown report keeps news as a global section.
- Announcement and research_report evidence are grouped under the watchlist stock evidence section.
- Grouping prefers query_code / query_name / query_market and falls back to stock_code / stock_name / symbol / company.
- Report generation reads Fast Evidence Pack only.
- No network request, probe rerun, PDF download, LLM call, or third-party dependency was used by this report step.
- Research report ratings and target prices are displayed as source metadata only.
