# Endpoint Probe Results

No endpoint probe has been executed in MVP0-001.

## MVP0-003 Eastmoney News Probe

Status: Success

Checked time: 2026-06-14T02:22:19.249939+08:00

Endpoint: https://np-weblist.eastmoney.com/comm/web/getFastNewsList?client=web&biz=web_724&fastColumn=102&sortEnd=&pageSize=10&req_trace=astockfastlane-6bc5ef5e8daa4155993c8645034f7fab

Request limit: 10 items, 1 request, timeout 10s

Output files:

- data/raw/eastmoney_news_probe_20260614.json
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

## MVP0-007G CNInfo Announcement Probe

Status: Success

Checked time: 2026-06-14T02:22:19.525385+08:00

Endpoint: https://www.cninfo.com.cn/new/hisAnnouncement/query

Method: POST

Request limit: 10 items, 1 request, timeout 15s

Probe stock: 688017

Output files:

- data/raw/cninfo_announcement_probe_20260614.json
- data/cache/cninfo_announcement_probe_latest.json

Observed fields:

- title
- publish_time
- company
- symbol
- announcement_type
- url
- raw

Notes:

- Parsed 10 item(s).
- Uses one CNInfo announcement endpoint only.
- Does not download announcement PDFs.
- No provider, pipeline, evidence pack, or report was generated.

## MVP0-008G Multi-source Fast Evidence Pack

Status: Success

Inputs:

- data/cache/eastmoney_news_probe_latest.json
- data/cache/cninfo_announcement_probe_latest.json

Output files:

- data/evidence/fast_evidence_pack_20260614.json
- data/evidence/fast_evidence_pack_latest.json

News item count: 10
Announcement item count: 10
Total evidence item count: 20

Notes:

- Built from cached Eastmoney news and CNInfo announcement probe JSON only.
- No network request was made.
- No Markdown report was generated.
- CNInfo announcement records are metadata only; PDFs were not downloaded.

## MVP0-009G+010G Markdown Report and Pipeline

Status: Success

Report input: data/evidence/fast_evidence_pack_latest.json

Output files:

- reports/fast_report_20260614.md
- reports/fast_report_latest.md

News item count: 10
Announcement item count: 10
Total evidence item count: 20

Notes:

- Markdown report supports news and announcement sections.
- Report generation reads Fast Evidence Pack only.
- No LLM call was made.
- Report does not provide investment advice.

## MVP0-011G MVP0 Release Documentation

Status: Success

Updated files:

- README.md
- docs/mvp0_release_notes.md
- docs/context_summary.md
- docs/current_progress.md
- docs/endpoint_probe_results.md
- scripts/check_project.py

Notes:

- This task did not run probes or the one-click pipeline.
- This task did not access the network.
- This task did not add new data sources.
- This task did not change probe or pipeline business logic.
