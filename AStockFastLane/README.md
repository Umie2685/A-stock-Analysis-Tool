# AStockFastLane

AStockFastLane is a lightweight A-share public-information collection and research-assistance project.

The current MVP2 version focuses on a small, auditable watchlist-based data chain:

```text
Eastmoney news + CNInfo announcements + Eastmoney research reports
-> Fast Evidence Pack
-> Markdown report
```

MVP2 moves from a fixed sample symbol to a configurable watchlist:

```text
config/watchlist.json -> watchlist announcement/report probes -> grouped Markdown report
```

本项目仅用于数据整理和研究辅助，不构成投资建议。

## Current Status

MVP2 has completed:

- Eastmoney global news minimal probe.
- CNInfo announcement minimal probe.
- Eastmoney research report minimal probe.
- Multi-source Fast Evidence Pack generation.
- Markdown report generation with news, announcement, and research_report sections.
- One-click MVP0 pipeline runner.
- Offline report-only runner.
- One-click MVP1 pipeline runner.
- MVP2 watchlist configuration and local validation tool.
- Watchlist CNInfo announcement and Eastmoney research report probes.
- Watchlist grouped Markdown report.
- One-click MVP2 pipeline runner.

The project is currently sealed at MVP2 scope. MVP3 should start from a small follow-up task rather than a broad redesign.

MVP3 has started with an offline local demo layer:

- `config/concept_map.json`: concept keyword and candidate watchlist mapping.
- `python scripts/analysis/analyze_hot_events.py`: offline rule-based hot event analysis.
- `python scripts/run_web_dashboard.py`: local standard-library web dashboard at `http://127.0.0.1:8000`.

MVP3 demo code reads existing local files only. It does not access the network, run probes, download or parse PDFs, call an LLM, introduce third-party dependencies, connect K-line/order-book/realtime quote data, or generate investment advice.

MVP3-005G improves the offline hot-event output quality while preserving those boundaries:

- `concept_map.json` now includes concept impact logic, typical positive/negative triggers, and risk notes.
- `related_stocks` include `role`, `relevance_score`, and `risk_note`; relevance score is concept relevance only, not investment value.
- `analyze_hot_events.py` analyzes news evidence only, keeps unmatched news events, ranks events by rule-based impact strength, and writes latest plus dated JSON/Markdown outputs.
- The Dashboard homepage displays hot event cards with impact direction, impact strength, related concepts, candidate watchlist stocks, transmission logic, risk notes, and `rule_based` analysis level.

MVP3-006G links the hot-event analysis output more tightly into the Dashboard:

- The homepage shows hot-event overview statistics, impact-strength counts, matched concepts, candidate watchlist count, a hot-event report link, and local data-health warnings.
- Hot events are grouped by `high`, `medium`, `low`, and `unknown` impact strength.
- Hot-event cards show matched keywords, impact logic, risk notes, and candidate watchlist stock details including `role`, `relevance_score`, and `risk_note`.
- `/hot-events-report` previews `reports/hot_events_latest.md` without running probes or regenerating reports.

MVP3-007G~010G completes the local hot-event to candidate-watchlist chain:

- `data/manual/hot_events_manual.json` adds an offline manual hot-event input source.
- `concept_map.json` now covers AI算力, 光通信, PCB, 数据中心, 有色金属, 消费电子, 创新药, 核电, 商业航天, 机器人, 半导体国产替代, 固态电池, 低空经济, and 军工.
- `analyze_hot_events.py` reads Evidence Pack news plus enabled manual hot events and preserves `input_source` as `evidence_news` or `manual_hot_event`.
- `scripts/analysis/build_candidate_watchlist.py` aggregates hot-event `related_stocks` into `candidate_watchlist_latest.json` and `candidate_watchlist_latest.md`.
- The Dashboard homepage links to `/candidate-watchlist`, which displays candidate observation stock cards sorted by `heat_score`.

## What This Project Does

- Fetches a small number of public news items from one Eastmoney fast-news endpoint.
- Fetches announcement metadata from one CNInfo announcement endpoint.
- Fetches research report metadata from one Eastmoney report endpoint.
- Saves raw and cache JSON for traceability.
- Normalizes news, announcement, and research_report items into a Fast Evidence Pack.
- Generates a Markdown report from the latest Evidence Pack.
- Preserves watchlist query metadata in announcement and research_report evidence items.
- Groups announcement and research_report evidence by watchlist stock in the Markdown report.

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
  config/
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

AStockFastLane uses only the Python standard library. No third-party runtime dependency is required yet.

```bash
python scripts/check_project.py
```

## Watchlist

The MVP2 watchlist lives at:

```text
config/watchlist.json
```

Watchlist fields:

- `code`: six-digit A-share symbol.
- `name`: stock name.
- `market`: optional market label such as `SH`, `SZ`, or `BJ`; missing values can be inferred by the loader.
- `enabled`: whether the symbol is included in watchlist probe batches.
- `orgId`: optional CNInfo organization id, useful for announcement queries.
- `note`: optional human note.

Validate it locally with:

```bash
python scripts/check_watchlist.py
```

The check reads the JSON file, validates enabled symbols, infers a missing market from the code prefix when possible, and prints the enabled code / name / market list. It does not access the network or run probes.

CNInfo announcements now read the enabled watchlist symbols:

```bash
python scripts/probes/test_cninfo_announcement_probe.py
```

Each announcement item includes query metadata such as `query_code`, `query_name`, `query_market`, and `query_orgId`. The probe fetches announcement metadata only and does not download or parse PDFs.

Eastmoney research reports also read the enabled watchlist symbols:

```bash
python scripts/probes/test_eastmoney_report_probe.py
```

Each report item includes `query_code`, `query_name`, and `query_market`. The probe fetches report metadata only; rating, target price, and institution opinion fields are preserved as source metadata and are not converted into investment advice.

## Offline Report Only

Run from the project root:

```bash
python scripts/run_offline_report.py
```

This entry reads only `data/evidence/fast_evidence_pack_latest.json` and regenerates:

```text
reports/fast_report_latest.md
reports/fast_report_YYYYMMDD.md
```

It does not run probes, access the network, rebuild the Evidence Pack, download PDFs, call an LLM, or generate investment advice.

## MVP3 Offline Hot Event Analysis

Run from the project root:

```bash
python scripts/analysis/analyze_hot_events.py
```

This entry reads:

```text
data/evidence/fast_evidence_pack_latest.json
config/concept_map.json
```

It writes:

```text
data/analysis/hot_events_latest.json
reports/hot_events_latest.md
data/analysis/hot_events_YYYYMMDD.json
reports/hot_events_YYYYMMDD.md
```

The analysis is a simple offline rule classifier. It reads news evidence only, matches concept keywords and candidate watchlist links from `config/concept_map.json`, and ranks events by concept hits, keyword hits, and strong trigger words such as policy, order, export control, and price-change terms. `related_stocks` are displayed only as candidate watchlist context for research assistance and are not converted into buy/sell guidance.

## MVP3 Local Web Dashboard

Run from the project root:

```bash
python scripts/run_web_dashboard.py
```

Then open:

```text
http://127.0.0.1:8000
```

The local dashboard displays:

- Project name.
- Enabled watchlist stocks.
- Evidence Pack counts for news / announcement / research_report / total.
- Data health warnings for the latest hot-event JSON, hot-event Markdown report, Evidence Pack, and Fast Report files.
- Hot event overview statistics, including total event count, impact-strength counts, matched concepts, and candidate watchlist count.
- Latest news items.
- Watchlist stock evidence grouped by stock.
- Hot event groups for `high`, `medium`, `low`, and `unknown`, with cards that include matched keywords, transmission logic, risk notes, and candidate watchlist stock metadata.
- `/hot-events-report` entry for previewing `reports/hot_events_latest.md`.
- Candidate observation stock overview and `/candidate-watchlist` entry.
- `fast_report_latest.md` entry and content preview.
- Research-only disclaimer.

The dashboard uses `http.server` from the Python standard library and reads local JSON/Markdown files only.

## One-click Run Entries

Report-only offline entry:

```bash
python scripts/run_offline_report.py
```

`run_offline_report.py` reads the existing `data/evidence/fast_evidence_pack_latest.json` and regenerates the Markdown reports. It does not access the network.

MVP1 compatibility refresh entry:

```bash
python scripts/run_mvp1_pipeline.py
```

`run_mvp1_pipeline.py` refreshes news + announcements + research reports, rebuilds the Evidence Pack, and regenerates the report.

MVP2 recommended watchlist refresh entry:

```bash
python scripts/run_mvp2_pipeline.py
```

`run_mvp2_pipeline.py` checks `config/watchlist.json`, refreshes news + watchlist announcements + watchlist research reports, rebuilds the Evidence Pack, and generates the grouped Markdown report.

## Legacy One-click Run

Run from the project root:

```bash
python scripts/run_mvp0_pipeline.py
```

The MVP0 one-click runner executes:

```text
scripts/probes/test_eastmoney_news_probe.py
scripts/probes/test_cninfo_announcement_probe.py
scripts/pipeline/build_fast_evidence_pack.py
scripts/pipeline/generate_fast_report.py
```

For the full MVP1 refresh, run:

```bash
python scripts/run_mvp1_pipeline.py
```

The MVP1 one-click runner executes:

```text
scripts/probes/test_eastmoney_news_probe.py
scripts/probes/test_cninfo_announcement_probe.py
scripts/probes/test_eastmoney_report_probe.py
scripts/pipeline/build_fast_evidence_pack.py
scripts/pipeline/generate_fast_report.py
```

This is the network refresh entry. It still does not download announcement PDFs, download research report PDFs, call an LLM, or generate investment advice.

For the MVP2 watchlist refresh, run:

```bash
python scripts/run_mvp2_pipeline.py
```

The MVP2 one-click runner executes:

```text
scripts/check_watchlist.py
scripts/probes/test_eastmoney_news_probe.py
scripts/probes/test_cninfo_announcement_probe.py
scripts/probes/test_eastmoney_report_probe.py
scripts/pipeline/build_fast_evidence_pack.py
scripts/pipeline/generate_fast_report.py
```

This is the recommended MVP2 network refresh entry. It does not download announcement PDFs, download research report PDFs, parse PDFs, call an LLM, or generate investment advice.

## Run Steps Manually

```bash
python scripts/probes/test_eastmoney_news_probe.py
python scripts/probes/test_cninfo_announcement_probe.py
python scripts/probes/test_eastmoney_report_probe.py
python scripts/pipeline/build_fast_evidence_pack.py
python scripts/pipeline/generate_fast_report.py
```

## Output Files

Probe outputs:

- `data/raw/eastmoney_news_probe_YYYYMMDD.json`
- `data/cache/eastmoney_news_probe_latest.json`
- `data/raw/cninfo_announcement_probe_YYYYMMDD.json`
- `data/cache/cninfo_announcement_probe_latest.json`
- `data/raw/eastmoney_report_probe_YYYYMMDD.json`
- `data/cache/eastmoney_report_probe_latest.json`

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
- `docs/mvp2_release_notes.md`: MVP2 release notes.
- `docs/context_summary.md`: continuation summary for future development or context compression.
- `docs/a_stock_data_reference.md`: reference notes for the a-stock-data project.

## Development Notes

- Keep request volume small.
- Use explicit timeout values for network probes.
- Save raw/cache outputs for traceability.
- Keep provider and pipeline changes scoped.
- Do not add investment advice or automatic trading logic.

## Suggested Next Step

Start MVP3 with a small, low-risk validation task, such as adding a dry-run summary command or a report schema audit, while preserving the no-investment-advice and no-automatic-trading boundaries.
