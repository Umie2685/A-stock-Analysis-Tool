# AStockFastLane

AStockFastLane is a lightweight A-share public-information collection and research-assistance project.

The current MVP0 version focuses on a small, auditable local data chain:

```text
Eastmoney news + CNInfo announcements -> Fast Evidence Pack -> Markdown report
```

本项目仅用于数据整理和研究辅助，不构成投资建议。

## Current Status

MVP0 has completed:

- Eastmoney global news minimal probe.
- CNInfo announcement minimal probe.
- Multi-source Fast Evidence Pack generation.
- Markdown report generation with news and announcement sections.
- One-click MVP0 pipeline runner.

## What This Project Does

- Fetches a small number of public news items from one Eastmoney fast-news endpoint.
- Fetches announcement metadata from one CNInfo announcement endpoint.
- Saves raw and cache JSON for traceability.
- Normalizes news and announcement items into a Fast Evidence Pack.
- Generates a Markdown report from the latest Evidence Pack.

## What This Project Does Not Do

- No investment advice.
- No automatic trading.
- No order placement or trading signals.
- No LLM integration.
- No Streamlit or web page.
- No database.
- No PDF bulk download.
- No high-frequency crawling.
- No full-market batch crawling.
- No access-control bypassing.

## Project Structure

```text
AStockFastLane/
  configs/
  data/
    raw/
    cache/
    evidence/
    manual/
  docs/
  reports/
  scripts/
    probes/
    pipeline/
    providers/
    utils/
```

## Install

MVP0 uses only the Python standard library. No third-party runtime dependency is required yet.

```bash
python scripts/check_project.py
```

## One-click Run

Run from the project root:

```bash
python scripts/run_mvp0_pipeline.py
```

The one-click runner executes:

```text
scripts/probes/test_eastmoney_news_probe.py
scripts/probes/test_cninfo_announcement_probe.py
scripts/pipeline/build_fast_evidence_pack.py
scripts/pipeline/generate_fast_report.py
```

## Run Steps Manually

```bash
python scripts/probes/test_eastmoney_news_probe.py
python scripts/probes/test_cninfo_announcement_probe.py
python scripts/pipeline/build_fast_evidence_pack.py
python scripts/pipeline/generate_fast_report.py
```

## Output Files

Probe outputs:

- `data/raw/eastmoney_news_probe_YYYYMMDD.json`
- `data/cache/eastmoney_news_probe_latest.json`
- `data/raw/cninfo_announcement_probe_YYYYMMDD.json`
- `data/cache/cninfo_announcement_probe_latest.json`

Evidence Pack outputs:

- `data/evidence/fast_evidence_pack_YYYYMMDD.json`
- `data/evidence/fast_evidence_pack_latest.json`

Report outputs:

- `reports/fast_report_YYYYMMDD.md`
- `reports/fast_report_latest.md`

Generated `data/` and `reports/` artifacts are ignored by Git by default.

## Documentation

- `docs/current_progress.md`: project progress log.
- `docs/endpoint_probe_results.md`: endpoint and pipeline result notes.
- `docs/mvp0_release_notes.md`: MVP0 release notes.
- `docs/context_summary.md`: continuation summary for future development or context compression.
- `docs/a_stock_data_reference.md`: reference notes for the a-stock-data project.

## Development Notes

- Keep request volume small.
- Use explicit timeout values for network probes.
- Save raw/cache outputs for traceability.
- Keep provider and pipeline changes scoped.
- Do not add investment advice or automatic trading logic.

## Suggested Next Step

MVP1-001G: add an Eastmoney research-report probe.
