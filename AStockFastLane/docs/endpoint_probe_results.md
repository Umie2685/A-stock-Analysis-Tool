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

## MVP4-005G Daily K and Trend Pipeline

Status: Success

Checked time: 2026-06-19T17:55:39.230173+08:00

Command:

```bash
python scripts/run_mvp4_pipeline.py --limit 20
```

Inputs:

- data/analysis/candidate_watchlist_latest.json

Steps:

- scripts/probes/test_daily_k_probe.py --limit 20
- scripts/analysis/analyze_trends.py

Output files:

- data/market/daily_k_latest.json
- data/market/daily_k_20260619.json
- data/analysis/trend_analysis_latest.json
- data/analysis/trend_analysis_20260619.json
- reports/trend_analysis_latest.md
- reports/trend_analysis_20260619.md

Daily K result:

- source: tencent_daily_k
- requested candidate limit: 20
- item count: 20
- ok count: 20
- failed count: 0

Trend analysis result:

- method: rule_based
- item count: 20
- ok count: 20
- unknown count: 0
- strong_uptrend: 0
- recovering: 9
- sideways: 4
- weakening: 6
- overheated: 1
- unknown: 0

Notes:

- The MVP4 pipeline accesses only the low-frequency daily K probe source, then runs local rule-based analysis.
- The pipeline does not start the Dashboard.
- No third-party dependency, PDF download, LLM call, order-book data, intraday data, high-frequency data, automatic trading, or trading output was added.

## MVP4-006G Sealing Audit

Status: Success

Checked time: 2026-06-19T18:15:01.123153+08:00

Commands:

```bash
git status --short
python -m py_compile scripts/run_mvp4_pipeline.py
python scripts/run_mvp4_pipeline.py --limit 20
python -m json.tool data/market/daily_k_latest.json
python -m json.tool data/analysis/trend_analysis_latest.json
python -m py_compile scripts/probes/test_daily_k_probe.py scripts/analysis/analyze_trends.py scripts/analysis/analyze_hot_events.py scripts/analysis/build_candidate_watchlist.py scripts/run_web_dashboard.py scripts/run_mvp2_pipeline.py
python scripts/run_web_dashboard.py
```

Core-chain result:

- daily_k source: tencent_daily_k
- daily_k item count: 20
- daily_k ok count: 20
- daily_k failed count: 0
- trend_analysis method: rule_based
- trend_analysis item count: 20
- trend_analysis ok count: 20
- trend_analysis unknown count: 0
- latest_trade_date distribution: 2026-06-18 = 20

Trend-state distribution:

- strong_uptrend: 0
- recovering: 9
- sideways: 4
- weakening: 6
- overheated: 1
- unknown: 0

Dashboard route check:

- /: HTTP 200
- /trend-analysis: HTTP 200
- /trend-analysis-report: HTTP 200
- /candidate-watchlist: HTTP 200
- /hot-events-report: HTTP 200

Workspace audit:

- Modified tracked docs: docs/current_progress.md, docs/endpoint_probe_results.md
- Modified tracked Dashboard file from MVP4 page work: scripts/run_web_dashboard.py
- New MVP4 script files remain untracked until a manual review stage.
- Generated data and report files remain in place and were not cleaned.

Notes:

- The audit accessed the network only through the existing low-frequency daily K probe.
- Dashboard service was stopped after validation and port 8000 was confirmed closed.
- Forbidden wording scan returned zero matches in the requested MVP4 audit scope.
- No feature code, trend rule, Dashboard business logic, new data source, dependency, commit, staging action, or file cleanup was performed by this sealing audit.
