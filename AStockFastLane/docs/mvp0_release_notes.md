# MVP0 Release Notes

## 1. Completed Features

- Eastmoney global news minimal probe.
- CNInfo announcement minimal probe.
- Multi-source Fast Evidence Pack generation.
- Markdown report generation with news and announcement sections.
- One-click MVP0 pipeline runner.
- Project skeleton and project check script.

## 2. Core Scripts

- `scripts/probes/test_eastmoney_news_probe.py`
  - Fetches a small batch of Eastmoney global fast-news items.
- `scripts/probes/test_cninfo_announcement_probe.py`
  - Fetches a small batch of CNInfo announcement metadata for one sample stock.
- `scripts/pipeline/build_fast_evidence_pack.py`
  - Builds a normalized Evidence Pack from cached probe outputs.
- `scripts/pipeline/generate_fast_report.py`
  - Generates Markdown reports from the latest Evidence Pack.
- `scripts/run_mvp0_pipeline.py`
  - Runs the MVP0 flow in sequence.
- `scripts/check_project.py`
  - Verifies required project files, directories, and basic JSON IO.

## 3. Inputs and Outputs

Inputs:

- `data/cache/eastmoney_news_probe_latest.json`
- `data/cache/cninfo_announcement_probe_latest.json`
- `data/evidence/fast_evidence_pack_latest.json`

Outputs:

- `data/raw/eastmoney_news_probe_YYYYMMDD.json`
- `data/raw/cninfo_announcement_probe_YYYYMMDD.json`
- `data/cache/eastmoney_news_probe_latest.json`
- `data/cache/cninfo_announcement_probe_latest.json`
- `data/evidence/fast_evidence_pack_YYYYMMDD.json`
- `data/evidence/fast_evidence_pack_latest.json`
- `reports/fast_report_YYYYMMDD.md`
- `reports/fast_report_latest.md`

## 4. Known Limits

- The probes use small request limits only.
- CNInfo announcement handling stores metadata only and does not download PDFs.
- The report is a data organization and research-assistance artifact, not investment advice.
- No LLM integration is included.
- No web page, database, scheduling, or automatic refresh is included.
- No provider abstraction or production pipeline hardening is included yet.
- Endpoint structures may change and should be rechecked before expanding coverage.

## 5. Compliance Notes

- This MVP does not implement automatic trading.
- This MVP does not provide buy, sell, or position suggestions.
- This MVP does not bypass access control or interface rate limits.
- This MVP keeps raw/cache outputs for traceability.

## 6. Next Stage Suggestions

- MVP1-001G: 接入东财研报 probe
- MVP1-002G: 研报并入 Evidence Pack
- MVP1-003G: 报告支持新闻 + 公告 + 研报
