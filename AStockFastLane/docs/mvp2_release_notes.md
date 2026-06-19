# MVP2 Release Notes

Status: Sealed

Date: 2026-06-14

## Purpose

MVP2 upgrades AStockFastLane from a fixed sample symbol flow to a configurable watchlist flow. The project remains a public-information collection and research-assistance tool. It does not provide investment advice, trading advice, trading signals, order placement, PDF parsing, or LLM-generated conclusions.

## Current Entrypoints

- `python scripts/run_offline_report.py`
  - Offline report-only entry.
  - Reads `data/evidence/fast_evidence_pack_latest.json`.
  - Regenerates `reports/fast_report_latest.md` and `reports/fast_report_YYYYMMDD.md`.
  - Does not access the network or run probes.
- `python scripts/run_mvp1_pipeline.py`
  - MVP1 compatibility refresh entry.
  - Refreshes news, announcements, research reports, Evidence Pack, and Markdown report.
  - Does not download PDFs or call an LLM.
- `python scripts/run_mvp2_pipeline.py`
  - MVP2 recommended refresh entry.
  - Checks `config/watchlist.json`.
  - Refreshes news, watchlist announcements, watchlist research reports, Evidence Pack, and grouped Markdown report.
  - Does not download PDFs or call an LLM.
- `python scripts/check_watchlist.py`
  - Local watchlist validation entry.
  - Does not access the network.
- `python scripts/pipeline/generate_fast_report.py`
  - Direct report-generation entry.
  - Reads the latest Evidence Pack and writes latest/dated Markdown reports.

## Current Data Flow

```text
config/watchlist.json
-> scripts/check_watchlist.py
-> scripts/probes/test_eastmoney_news_probe.py
-> scripts/probes/test_cninfo_announcement_probe.py
-> scripts/probes/test_eastmoney_report_probe.py
-> data/cache/*_latest.json + data/raw/*_YYYYMMDD.json
-> scripts/pipeline/build_fast_evidence_pack.py
-> data/evidence/fast_evidence_pack_latest.json + data/evidence/fast_evidence_pack_YYYYMMDD.json
-> scripts/pipeline/generate_fast_report.py
-> reports/fast_report_latest.md + reports/fast_report_YYYYMMDD.md
```

News remains global. Announcement and research report evidence preserve watchlist query metadata and are grouped by stock in the Markdown report.

## MVP2 Completed Capabilities

- Added `config/watchlist.json` and `config/watchlist.example.json`.
- Added standard-library watchlist loading and validation.
- Added `scripts/check_watchlist.py`.
- Upgraded CNInfo announcement probe to read enabled watchlist symbols.
- Upgraded Eastmoney research report probe to read enabled watchlist symbols.
- Preserved `query_code`, `query_name`, and `query_market` in downstream announcement and research report evidence.
- Preserved announcement `query_orgId` when available.
- Upgraded Markdown report with `观察池个股证据` grouped by stock.
- Added `scripts/run_mvp2_pipeline.py`.
- Kept `run_offline_report.py` and `run_mvp1_pipeline.py` working.
- Kept all runtime code on the Python standard library.

## Current Git Status Classification

Expected MVP2 source/documentation changes:

- `README.md`
- `docs/current_progress.md`
- `docs/endpoint_probe_results.md`
- `docs/cninfo_watchlist_probe_notes.md`
- `docs/eastmoney_report_watchlist_probe_notes.md`
- `docs/fast_evidence_pack_watchlist_notes.md`
- `docs/mvp2_watchlist_report_notes.md`
- `docs/mvp2_release_notes.md`
- `config/watchlist.json`
- `config/watchlist.example.json`
- `scripts/check_watchlist.py`
- `scripts/utils/watchlist_loader.py`
- `scripts/probes/test_cninfo_announcement_probe.py`
- `scripts/probes/test_eastmoney_report_probe.py`
- `scripts/pipeline/build_fast_evidence_pack.py`
- `scripts/pipeline/generate_fast_report.py`
- `scripts/run_offline_report.py`
- `scripts/run_mvp1_pipeline.py`
- `scripts/run_mvp2_pipeline.py`

Generated runtime artifacts from validation runs:

- `data/cache/*_latest.json`
- `data/raw/*_20260614.json`
- `data/evidence/fast_evidence_pack_latest.json`
- `data/evidence/fast_evidence_pack_20260614.json`
- `reports/fast_report_latest.md`
- `reports/fast_report_20260614.md`

Historical or auxiliary items to review separately:

- `docs/handoff_for_new_chat.md`
- `docs/eastmoney_report_endpoint_notes.md`
- `../tmp_stock_docs/`

No destructive cleanup was performed. Generated `data/` and `reports/` files are currently ignored by `.gitignore`, but some appear as modified because they were already tracked before the ignore rule or earlier tasks.

## MVP3 Starting Points

Prefer a small first MVP3 task. Good candidates:

- Add a `scripts/check_pipeline_state.py` command that summarizes watchlist, cache, Evidence Pack, and report freshness without network access.
- Add a schema audit for Evidence Pack items, checking required fields for news, announcement, and research_report.
- Add a report snapshot check that verifies required Markdown sections and no-advice keywords.
- Add a dry-run mode to `run_mvp2_pipeline.py` that prints planned steps without executing probes.

Avoid starting MVP3 with broad UI, LLM integration, or large multi-stock crawling until the local state checks are stable.

## Boundaries Preserved

- No investment advice.
- No automatic trading.
- No order placement.
- No PDF download.
- No PDF parsing.
- No LLM call.
- No third-party dependency.
- No evidence type change beyond `news`, `announcement`, and `research_report`.
