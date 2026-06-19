# Current Progress

## MVP0-001

Status: Created project skeleton.

## Done

- Created base directories.
- Created placeholder configs.
- Created minimal IO utilities.
- Created project check script.

## Not Started

- Eastmoney news probe.
- CNInfo announcement probe.
- Eastmoney report probe.
- Fast Evidence Pack.
- Markdown report generation.

## MVP0-002

Status: Completed

Summary:

- Reviewed a-stock-data README.md / SKILL.md.
- Created docs/a_stock_data_reference.md.
- Identified MVP-0 candidate endpoints.
- Confirmed no third-party code was copied.

Next:

- MVP0-003: Eastmoney news minimal probe.

## MVP0-003

Status: Completed

Summary:

- Implemented Eastmoney news minimal probe.
- Generated raw/cache JSON.
- Updated endpoint probe results.

Next:

- MVP0-004: Fast Evidence Pack minimal generation.

## MVP0-003S

Status: Partially Completed

Summary:

- Attempted to install and verify a-stock-data Skill.
- Created installation notes.
- Created usage plan.
- Updated project direction to Skill-centric development.

Next:

- MVP0-004S: Use Skill to identify Eastmoney news endpoint.

## Eastmoney News Minimal Source Loop

Status: Completed

Summary:

- Confirmed Eastmoney global news endpoint from local installed a-stock-data SKILL.md.
- Implemented / aligned the minimal Eastmoney news probe with the Skill-documented endpoint shape.
- Generated raw/cache JSON for the news probe.
- Added docs/eastmoney_news_endpoint_notes.md.
- Updated endpoint probe results.

Next:

- MVP0-005G: Fast Evidence Pack minimal generation.

## MVP0-005G

Status: Completed

Summary:

- Built minimal Fast Evidence Pack from Eastmoney news probe.
- Generated latest and dated evidence JSON.
- No network request was made.

Next:

- MVP0-006G: Generate Markdown hotspot report.

## MVP0-006G

Status: Completed

Summary:

- Generated Markdown fast report from Fast Evidence Pack.
- Created latest and dated report files.
- No network request or LLM call was made.

Next:

- MVP0-007G: Add CNInfo announcement source.

## MVP0-007G

Status: Completed

Summary:

- Confirmed one CNInfo announcement endpoint from local a-stock-data SKILL.md.
- Implemented CNInfo announcement minimal probe.
- Generated raw/cache announcement JSON.
- No PDF download, Evidence Pack generation, report generation, or investment advice was produced.

Next:

- MVP0-008G: Merge CNInfo announcements into Fast Evidence Pack.

## MVP1-001G

Status: Completed

Summary:

- Confirmed one Eastmoney reportapi endpoint from the local a-stock-data Skill.
- Implemented Eastmoney report minimal probe.
- Generated raw/cache report metadata JSON.
- Updated Eastmoney report endpoint notes and endpoint probe results.
- No PDF download, Evidence Pack generation, Markdown report generation, or investment advice was produced.

Next:

- MVP1-002G: 将东财研报并入 Fast Evidence Pack

## MVP1-002G

Status: Completed

Summary:

- Merged Eastmoney news, CNInfo announcements, and Eastmoney reports into Fast Evidence Pack.
- Generated latest and dated evidence JSON.
- No network request was made.

Next:

- MVP1-003G: Upgrade Markdown report to support news + announcements + research reports.

## MVP1-003G

Status: Completed

Summary:

- Upgraded Markdown report generation for news + announcements + research reports.
- Report generation reads data/evidence/fast_evidence_pack_latest.json only.
- Generated latest and dated Markdown reports.
- Announcement PDF and research report PDF files were not downloaded or parsed.
- Research report rating fields are displayed only as original source metadata.

Next:

- MVP1 follow-up: continue improving local research-assistance workflow without changing the no-investment-advice boundary.

## MVP1-004G

Status: Completed

Summary:

- Added scripts/run_offline_report.py as the report-only offline entry.
- The offline entry reads data/evidence/fast_evidence_pack_latest.json and regenerates latest and dated Markdown reports.
- It does not run probes, access the network, rebuild the Evidence Pack, download PDFs, call an LLM, or generate investment advice.

Next:

- MVP1-005G: Add a one-click MVP1 pipeline runner.

## MVP1-005G

Status: Completed

Summary:

- Added scripts/run_mvp1_pipeline.py as the one-click MVP1 refresh entry.
- The pipeline runs Eastmoney news, CNInfo announcement, Eastmoney research report, Fast Evidence Pack build, and Markdown report generation in order.
- The pipeline stops on the first failed step and returns the failing exit code.
- It prints final report paths and news / announcement / research_report / total evidence counts.
- The pipeline does not add PDF download, LLM calls, third-party dependencies, or investment advice generation.

Next:

- Continue MVP1 with focused research-assistance improvements and keep offline/report-only workflows separate from network refresh workflows.

## MVP2-001G

Status: Completed

Summary:

- Added config/watchlist.json with the default MVP1 sample symbol 688017 / 绿的谐波.
- Added config/watchlist.example.json with enabled and disabled examples.
- Added scripts/utils/watchlist_loader.py for standard-library JSON loading, validation, enabled filtering, and market inference.
- Added scripts/check_watchlist.py as a local command-line validation entry.
- No network request, probe run, Evidence Pack change, report logic change, PDF download, LLM call, third-party dependency, or investment advice was added.

Next:

- MVP2 follow-up: update future probes to read enabled symbols from the watchlist before adding multi-symbol batch processing.

## MVP2-002G

Status: Completed

Summary:

- Upgraded the CNInfo announcement probe to read enabled symbols from config/watchlist.json.
- Added per-symbol query metadata fields: query_code, query_name, query_market, and query_orgId.
- The probe records per-stock failures without crashing the whole batch.
- Generated latest and dated CNInfo announcement probe JSON.
- No announcement PDF download, PDF parsing, LLM call, third-party dependency, evidence logic change, report logic change, or investment advice was added.

Next:

- MVP2 follow-up: adapt downstream evidence building only if multi-symbol output needs additional compatibility.

## MVP2-003G

Status: Completed

Summary:

- Upgraded the Eastmoney report probe to read enabled symbols from config/watchlist.json.
- Added per-symbol query metadata fields: query_code, query_name, and query_market.
- The probe records per-stock failures without crashing the whole batch.
- Generated latest and dated Eastmoney report probe JSON.
- No report PDF download, full-text parsing, LLM call, third-party dependency, evidence logic change, report logic change, or investment advice was added.
- Rating, target price, and institution opinion fields remain source metadata only.

Next:

- MVP2 follow-up: adapt downstream evidence building only if multi-symbol report output needs additional compatibility.

## MVP2-004G

Status: Completed

Summary:

- Upgraded scripts/pipeline/build_fast_evidence_pack.py to preserve watchlist query metadata from announcement and research report cache items.
- Announcement evidence items now include query_code, query_name, query_market, query_orgId, stock_code, and stock_name when available.
- Research report evidence items now include query_code, query_name, query_market, stock_code, and stock_name when available.
- Added evidence_type alongside the existing category field for news / announcement / research_report compatibility.
- Rebuilt latest and dated Fast Evidence Pack from local cache only.
- No network request, probe run, PDF download, LLM call, third-party dependency, report logic change, or investment advice was added.

Next:

- MVP2 follow-up: verify Markdown reporting remains sufficient with the enriched evidence fields, then consider multi-symbol report display improvements only if needed.

## MVP2-005G

Status: Completed

Summary:

- Upgraded Markdown report generation with a watchlist stock evidence section.
- News evidence remains global.
- Announcement and research_report evidence are grouped by query_code / query_name / query_market with stock field fallbacks.
- Research report rating and target_price fields are displayed only as original source metadata.
- No PDF download, LLM call, third-party dependency, or investment advice generation was added.

Next:

- MVP2-006G: add a one-click MVP2 pipeline runner.

## MVP2-006G

Status: Completed

Summary:

- Added scripts/run_mvp2_pipeline.py as the recommended MVP2 refresh entry.
- The pipeline checks config/watchlist.json before running probe steps.
- It refreshes news, watchlist CNInfo announcements, watchlist Eastmoney research reports, Fast Evidence Pack, and grouped Markdown report in order.
- The pipeline stops on the first failed step and returns the failing exit code.
- It prints latest evidence/report paths and news / announcement / research_report / total counts after success.
- It does not add PDF download, LLM calls, third-party dependencies, or investment advice generation.

Next:

- MVP2-007G: keep README and progress docs aligned with the three run entries.

## MVP2-007G

Status: Completed

Summary:

- Documented run_offline_report.py, run_mvp1_pipeline.py, and run_mvp2_pipeline.py.
- Documented config/watchlist.json and the code / name / market / enabled / orgId / note fields.
- Added docs/mvp2_watchlist_report_notes.md for the watchlist grouped report and MVP2 pipeline boundary.

Next:

- MVP2 can now proceed to larger watchlist batches while keeping source metadata and no-advice boundaries explicit.

## MVP2-FINAL

Status: Completed

Summary:

- Sealed MVP2 scope with docs/mvp2_release_notes.md.
- Clarified current run entries, current data flow, completed MVP2 capabilities, git status classification, and safe MVP3 starting points.
- Updated README.md from MVP1-current wording to MVP2-current wording.
- No probe, Evidence Pack, report generation logic, PDF download, LLM call, third-party dependency, or investment advice logic was added in this final cleanup step.

Next:

- Start MVP3 with a small local validation task before larger workflow changes.

## MVP3-001G

Status: Completed

Summary:

- Added `scripts/run_web_dashboard.py` as a local standard-library web dashboard.
- The dashboard serves `http://127.0.0.1:8000` by default.
- The homepage displays project name, enabled watchlist stocks, Evidence Pack counts, latest news, watchlist grouped announcement/report evidence, hot event analysis entry, Fast Report preview, and a research-only disclaimer.
- The dashboard reads local JSON/Markdown files only.
- No network request, probe run, PDF download, PDF parsing, LLM call, third-party dependency, K-line data, order-book data, realtime quote data, trading signal, or investment advice was added.

Next:

- Continue MVP3 with offline hot event analysis outputs and documentation.

## MVP3-002G

Status: Completed

Summary:

- Added `scripts/analysis/analyze_hot_events.py` as an offline rule-based hot event analyzer.
- The analyzer reads `data/evidence/fast_evidence_pack_latest.json` and `config/concept_map.json`.
- It classifies evidence items by concept keywords and candidate watchlist stock links.
- It writes `data/analysis/hot_events_latest.json` and `reports/hot_events_latest.md`.
- The generated fields keep classification method, related concepts, related stock examples, source evidence ids, and a research-only disclaimer.
- No network request, probe run, PDF download, PDF parsing, LLM call, third-party dependency, trading signal, or investment advice was added.

Next:

- Keep concept mapping small and auditable before adding larger data sources.

## MVP3-003G

Status: Completed

Summary:

- Added `config/concept_map.json`.
- Initial concepts include 人形机器人, 半导体国产替代, 固态电池, 人工智能, 低空经济, and 军工.
- `related_stocks` are documented and used only as candidate watchlist links for research context.
- No related stock entry is treated as a buy recommendation.

Next:

- Expand the concept map only with explicit small-scope review.

## MVP3-004G

Status: Completed

Summary:

- Generated offline hot event JSON and Markdown report outputs.
- The latest JSON output is `data/analysis/hot_events_latest.json`.
- The latest Markdown output is `reports/hot_events_latest.md`.
- Outputs are generated from existing local Evidence Pack data and local concept mapping only.
- The Markdown report includes matched concepts, hot event rows, candidate watchlist examples, and a disclaimer.

Next:

- Verify the full no-network MVP3 demo flow and keep the current MVP2 probe pipeline unchanged.

## MVP3-005G

Status: Completed

Summary:

- Enhanced `config/concept_map.json` with `impact_logic`, `typical_positive_triggers`, `typical_negative_triggers`, and `risk_notes` for each concept.
- Enhanced each configured `related_stock` with `role`, `relevance_score`, and `risk_note`; the score is concept relevance only and does not represent investment value.
- Updated `scripts/analysis/analyze_hot_events.py` to analyze news evidence only, preserve unmatched news events, rank by rule-based impact strength, and generate latest plus dated hot-event JSON/Markdown outputs.
- Hot-event JSON now includes `impact_logic`, `risk_notes`, `positive_triggers`, `negative_triggers`, `impact_direction`, `impact_strength`, `reason`, and `analysis_level: rule_based`.
- Updated `reports/hot_events_latest.md` generation to show transmission logic, risk notes, candidate watchlist stocks, relevance score, rule-hit keywords, and rule judgment reason.
- Updated `scripts/run_web_dashboard.py` with hot-event cards on the homepage.
- Added `docs/mvp3_hot_events_quality_notes.md`.
- No network request, probe run, MVP2 pipeline run, PDF download, PDF parsing, LLM call, third-party dependency, K-line data, order-book data, realtime quote data, automatic trading, or investment advice was added.

Next:

- Keep the hot-event rule set auditable before adding any new live data source or model layer.

## MVP3-006G

Status: Completed

Summary:

- Enhanced `scripts/run_web_dashboard.py` so the homepage displays hot-event overview statistics, impact-strength counts, matched concepts, candidate watchlist count, and a link to the latest hot-event Markdown report.
- Added data-health warnings for the latest hot-event JSON, latest hot-event Markdown report, latest Evidence Pack, and latest Fast Report files; missing files render warnings instead of crashing the page.
- Grouped hot events by `high`, `medium`, `low`, and `unknown` impact strength.
- Expanded hot-event cards to show matched keywords, impact logic, risk notes, `analysis_level`, and candidate watchlist stock details including `role`, `relevance_score`, `reason`, and `risk_note`.
- Added `/hot-events-report` to preview `reports/hot_events_latest.md` from local disk.
- No network request, probe run, MVP2 pipeline run, PDF download, PDF parsing, LLM call, third-party dependency, K-line data, order-book data, realtime quote data, automatic trading, or investment advice was added.

Next:

- Keep Dashboard improvements local and read-only unless a future task explicitly refreshes data outputs.

## MVP3-007G~010G

Status: Completed

Summary:

- Added `data/manual/hot_events_manual.json` and `data/manual/hot_events_manual.example.json` as the offline manual hot-event input source.
- Extended `config/concept_map.json` to cover AI算力, 光通信, PCB, 数据中心, 有色金属, 消费电子, 创新药, 核电, 商业航天, 机器人, 半导体国产替代, 固态电池, 低空经济, and 军工.
- Updated `scripts/analysis/analyze_hot_events.py` to read Evidence Pack news plus enabled manual hot events, preserve `input_source`, and map matched concepts to candidate observation stocks.
- Added `scripts/analysis/build_candidate_watchlist.py` to aggregate hot-event related stocks by code, calculate `heat_score`, mark `in_watchlist`, and write latest plus dated JSON/Markdown outputs.
- Updated `scripts/run_web_dashboard.py` with a homepage candidate-watchlist entry and `/candidate-watchlist` page.
- Generated `data/analysis/candidate_watchlist_latest.json` and `reports/candidate_watchlist_latest.md`.
- No network request, probe run, MVP2 pipeline run, PDF download, PDF parsing, LLM call, third-party dependency, K-line data, order-book data, realtime quote data, automatic trading, or investment advice was added.

Next:

- Keep candidate-watchlist generation offline and auditable; future changes should treat candidates as research context only.

## MVP4-001G

Status: Completed

Summary:

- Added `docs/mvp4_market_data_schema.md` for low-frequency daily K schema planning.
- Added `data/market/.gitkeep` and `data/market/daily_k_latest.example.json`.
- Defined raw market fields, normalized fields, future trend-analysis fields, data-quality states, and the trend-state enum.
- No network request, Dashboard change, trend analyzer, order-book data, high-frequency data, automatic trading, or trading output was added.

Next:

- Implement a minimal candidate-stock daily K probe with structured failure rows.

## MVP4-002G

Status: Completed

Summary:

- Added `scripts/probes/test_daily_k_probe.py`.
- The probe reads `data/analysis/candidate_watchlist_latest.json`, fetches low-frequency Tencent daily K data, and writes latest plus dated JSON outputs under `data/market/`.
- Supports `--limit`, `--days`, `--source`, and `--adjust-type`.
- Preserves one structured result per candidate and marks unsupported market, fetch, parse, insufficient-history, and empty-bars cases without stopping the whole run.
- No third-party dependency, order-book data, intraday data, high-frequency data, automatic trading, or trading output was added.

Next:

- Build an offline rule-based trend analyzer on top of `data/market/daily_k_latest.json`.

## MVP4-003G

Status: Completed

Summary:

- Added `scripts/analysis/analyze_trends.py`.
- The analyzer reads `data/market/daily_k_latest.json`, computes MA5 / MA10 / MA20, short-window close changes, relative volume, and distance from the 20-day high.
- Writes `data/analysis/trend_analysis_latest.json`, dated trend JSON, `reports/trend_analysis_latest.md`, and a dated Markdown report.
- Uses only the rule-based states `strong_uptrend`, `recovering`, `sideways`, `weakening`, `overheated`, and `unknown`.
- Keeps conclusions as trend-state context for research assistance only.

Next:

- Add a local Dashboard page for the generated trend-analysis output.

## MVP4-004G

Status: Completed

Summary:

- Updated `scripts/run_web_dashboard.py` with `/trend-analysis`.
- Added `/trend-analysis-report` and `/trend-analysis.md` report-preview routes for `reports/trend_analysis_latest.md`.
- The homepage now links to the short-term trend-analysis page and shows a compact trend-analysis module.
- Missing or malformed trend JSON shows a friendly local-command prompt instead of crashing the service.
- No network request, Dashboard auto-refresh, third-party dependency, order-book data, high-frequency data, automatic trading, or trading output was added.

Next:

- Add a one-click MVP4 pipeline that runs daily K refresh and offline trend analysis without starting the Dashboard.

## MVP4-005G

Status: Completed

Summary:

- Added `scripts/run_mvp4_pipeline.py` as the one-click MVP4 generation entry.
- The pipeline checks `data/analysis/candidate_watchlist_latest.json`, runs `scripts/probes/test_daily_k_probe.py --limit N`, then runs `scripts/analysis/analyze_trends.py`.
- Default candidate limit is 20; it can be changed with `--limit`.
- It checks for `data/market/daily_k_latest.json`, `data/analysis/trend_analysis_latest.json`, and `reports/trend_analysis_latest.md`.
- It prints daily K counts, trend-analysis counts, state counts, output paths, and the next Dashboard command.
- Verification with `--limit 20` generated 20 daily K rows and 20 trend-analysis rows: `recovering=9`, `sideways=4`, `weakening=6`, `overheated=1`, `strong_uptrend=0`, `unknown=0`.
- The pipeline does not start the Dashboard and does not modify MVP0-MVP3 entrypoints.

Run:

```bash
python scripts/run_mvp4_pipeline.py --limit 20
python scripts/run_web_dashboard.py
```

Dashboard pages:

```text
/trend-analysis
/trend-analysis-report
/trend-analysis.md
```

Boundary:

- MVP4 is for public-information organization and research assistance only.
- Trend analysis is `rule_based`.
- It does not provide investment advice, automatic trading, order placement, order-book data, intraday data, or high-frequency data.

Next:

- Keep MVP4 output auditable before adding any larger data source or model layer.

## MVP4-006G

Status: Completed

Summary:

- Completed the MVP4 sealing audit and handoff pass.
- Re-ran `python scripts/run_mvp4_pipeline.py --limit 20`.
- Re-validated `data/market/daily_k_latest.json` and `data/analysis/trend_analysis_latest.json` with `python -m json.tool`.
- Recompiled MVP4 and regression entrypoints, including `scripts/run_mvp2_pipeline.py`.
- Verified Dashboard routes `/`, `/trend-analysis`, `/trend-analysis-report`, `/candidate-watchlist`, and `/hot-events-report` returned HTTP 200.
- Added `docs/handoff_for_mvp5_new_chat.md` for the next chat.
- No feature code, trend rule, Dashboard business logic, new data source, third-party dependency, or cleanup of untracked files was added.

Audit result:

```text
daily_k item_count: 20
daily_k ok_count: 20
daily_k failed_count: 0
trend_analysis item_count: 20
trend_analysis ok_count: 20
trend_analysis unknown_count: 0
latest_trade_date distribution: 2026-06-18 = 20
```

Trend-state distribution:

```text
strong_uptrend: 0
recovering: 9
sideways: 4
weakening: 6
overheated: 1
unknown: 0
```

Dashboard audit:

```text
/                          HTTP 200
/trend-analysis            HTTP 200
/trend-analysis-report     HTTP 200
/candidate-watchlist       HTTP 200
/hot-events-report         HTTP 200
```

Boundary:

- MVP4 remains a public-information and rule-based research-assistance workflow.
- It does not include automatic trading, order placement, realtime order-book data, intraday data, or high-frequency data.
- MVP4 is ready to seal.

Next:

- Start MVP5 from `docs/handoff_for_mvp5_new_chat.md` with a small planning-only task.

## MVP5-001G

Status: Completed

Summary:

- Audited the current candidate generation mechanism from hot-event inputs to `candidate_watchlist_latest.json`.
- Documented the current `heat_score` formula, candidate fields, sorting rule, and which fields are explanatory only.
- Documented how `config/concept_map.json` controls concept matching and candidate stock links.
- Added `docs/mvp5_candidate_filtering_audit.md`.
- Added `config/user_stock_preferences.json` and `config/user_stock_preferences.example.json` for future candidate-review filtering.
- Preserved the MVP5 boundary: no candidate-generation logic change, no Dashboard change, no watchlist change, no network access, no new runtime dependency, and no automatic synchronization.

Next:

- MVP5-002G: design or implement a local `candidate_review` generator that reads candidate, trend, and user-preference files, writes review outputs, and keeps manual confirmation before any watchlist synchronization.

## MVP5-002G

Status: Completed

Summary:

- Added `scripts/analysis/build_candidate_review.py` as the local rule-based candidate review generator.
- The generator reads `data/analysis/candidate_watchlist_latest.json`, `data/analysis/trend_analysis_latest.json`, and `config/user_stock_preferences.json`.
- It writes latest plus dated JSON and Markdown outputs for `candidate_review`.
- It calculates `raw_heat_score`, `preference_score`, `trend_score`, `risk_penalty`, and `final_score`.
- It assigns only the approved review buckets: `core_watch`, `elastic_watch`, `trend_watch`, `market_height_watch`, `skip`, `blocked`, and `unknown`.
- It respects `review_limits.daily_review_limit` and the initial bucket quotas from the preference config.
- It keeps `manual_confirm_required=true` on each item and does not modify `config/watchlist.json`.
- No Dashboard change, MVP4 pipeline change, network access, third-party dependency, or automatic synchronization was added.

Run:

```bash
python scripts/analysis/build_candidate_review.py
```

Outputs:

```text
data/analysis/candidate_review_latest.json
reports/candidate_review_latest.md
```

Next:

- MVP5-003G: add a local Dashboard read-only page for `candidate_review_latest.json` and `candidate_review_latest.md`, without adding synchronization.

## MVP5-003G

Status: Completed

Summary:

- Updated `scripts/run_web_dashboard.py` with read-only `candidate_review` Dashboard display.
- Added Dashboard routes `/candidate-review`, `/candidate-review-report`, and `/candidate-review.md`.
- Added the candidate-review JSON and Markdown files to Dashboard health checks.
- Added the `候选审核池` navigation entry and homepage candidate-review summary.
- The candidate-review page reads `data/analysis/candidate_review_latest.json` and displays selected review items, bucket counts, all review buckets, selection notes, disabled themes, risk notes, and data-health errors.
- The candidate-review report route previews `reports/candidate_review_latest.md`.
- Preserved the MVP5 boundary: no `config/watchlist.json` change, no watchlist synchronization UI, no Dashboard write action, no candidate-review generation logic change, no network access, no new dependency, and no MVP4 pipeline change.

Dashboard routes:

```text
/candidate-review
/candidate-review-report
/candidate-review.md
```

Next:

- MVP5-004G: design a manual confirmation workflow or review-status schema, still without writing to `config/watchlist.json` automatically.

## MVP5-004G

Status: Completed

Summary:

- Added `data/manual/candidate_review_status.example.json` and `data/manual/candidate_review_status.json` as the local manual review-status schema for `candidate_review`.
- The schema keeps `sync_mode=manual_confirm`, `confirmed_by_user=false` by default, and does not auto-sync to `config/watchlist.json`.
- No Dashboard, candidate-review generator, watchlist, network, dependency, or trading workflow change was added.

Next:

- MVP5-005G: add a read-only Dashboard preview for manual review status, or design the later manual-confirm sync gate without enabling automatic watchlist writes.

## MVP5-005G

Status: Completed

Summary:

- Updated `scripts/run_web_dashboard.py` so `/candidate-review` and the homepage read `data/manual/candidate_review_status.json` in read-only mode.
- Candidate-review cards now show manual review status fields with safe defaults when no local status exists.
- No status-file write action, watchlist synchronization, Dashboard button, candidate-review generator change, network access, dependency, or trading workflow change was added.

Next:

- MVP5-006G: consider a read-only status summary or a separately reviewed manual-confirm gate before any future watchlist update workflow.

## MVP5-006G to MVP5-009G

Status: Completed

Summary:

- MVP5-006G completed: added `scripts/manual/update_candidate_review_status.py` for manual local status updates.
- MVP5-007G completed: added `scripts/reports/build_daily_after_close_report.py` and generated latest plus dated daily after-close JSON and Markdown reports.
- MVP5-008G completed: updated Dashboard with `/daily-report`, `/daily-report-report`, `/daily-report.md`, navigation entry, and homepage summary.
- MVP5-009G regression completed: watchlist was not auto-written, `candidate_review_status` can be manually updated, and `daily_after_close_report` is generated and displayed.

Next:

- MVP5 follow-up can add a guarded manual-confirm workflow, but it should remain separate from automatic watchlist writes.

## MVP6-001G

Status: Completed

Summary:

- Updated `scripts/run_web_dashboard.py` with a Dashboard UI foundation for the local research console.
- Reworked the homepage into a concise research-console view: key takeaways, daily report summary, candidate-review focus list, hot mainlines, and data health/update times.
- Added a shared page-header component and refreshed card, badge, panel, warning, disclaimer, detail-grid, navigation, and responsive layout styles.
- Renamed Dashboard wording so `candidate_watchlist` is shown as the hot-event candidate pool, while `watchlist` remains the long-term manual observation pool.
- Preserved MVP6 boundaries: no data-generation logic changes, no network access, no new dependency, no watchlist write, and no sync entry.

Next:

- MVP6-002G can refine individual page layouts or add non-writing filters/search for daily review ergonomics.

## MVP6 Handoff

Status: Completed

Summary:

- Added `docs/handoff_for_mvp6_new_chat.md` as the new-chat handoff for continuing MVP6 Dashboard development.
- The handoff records current Dashboard state, routes, verification snapshot, data-flow files, boundaries, and a suggested MVP6-002G next task.

## MVP6-002G

Status: Completed

Summary:

- Updated `scripts/run_web_dashboard.py` with unified Dashboard datetime display so ISO strings are rendered as compact local timestamps.
- Added standard-library Markdown report rendering for headings, lists, tables, paragraphs, and fenced code blocks.
- Improved `/candidate-watchlist` readability by keeping the source JSON path out of large stat cards and retaining the distinction between `candidate_watchlist` and long-term `watchlist`.
- Preserved MVP6 boundaries: no network access, no new dependency, no JSON generation change, no watchlist write, no sync entry, and no trading workflow change.

## MVP6-003G

Status: Completed

Summary:

- Optimized `/candidate-review` into a more review-oriented read-only page.
- Added bucket navigation and grouped candidate-review sections for core, elastic, market-height, trend, skip, blocked, and unknown buckets.
- Reworked candidate-review cards to emphasize final score, review bucket, trend state, manual status, score components, selection reasons, themes, risk notes, observation notes, trend metrics, and source events.
- Kept the homepage compact by showing candidate-review overview plus selected review cards without expanding all bucket sections.
- Preserved MVP6 boundaries: no network access, no new dependency, no JSON generation change, no watchlist write, no sync entry, and no trading workflow change.

## MVP6-003G-KLINE

Status: Completed

Summary:

- Added read-only daily K integration for `/candidate-review` from `data/market/daily_k_latest.json`.
- Added inline standard-library SVG rendering for recent daily candlesticks and volume bars inside each full candidate-review trend block when daily K bars are available.
- Missing or insufficient K-line data now falls back to a small empty-state message without failing page rendering.
- Preserved MVP6 boundaries: no network access, no new dependency, no JSON generation change, no watchlist write, no sync entry, and no trading workflow change.

## MVP6-003G-KLINE-UX

Status: Completed

Summary:

- Diagnosed visually broken K-line cases such as 002837 as unadjusted daily K discontinuities from `adjust_type: none`, with large price gaps around ex-right/dividend-like events.
- Enhanced the inline SVG K-line chart with hover bands, crosshair cursor feedback, and per-day tooltip data including open, close, high, low, computed pct change, and volume.
- Added large-gap detection and an in-chart note for suspected unadjusted/ex-right discontinuities.
- Adjusted candidate-review card layout so theme and trend blocks span the full card width, reducing the empty stretched left-card area after adding charts.
- Moved the top navigation into a left-side auto-reveal navigation rail that stays hidden by default and expands on hover/focus.
- Preserved MVP6 boundaries: no network access, no new dependency, no JSON generation change, no watchlist write, no sync entry, and no trading workflow change.

## MVP6-003G-QFQ-LAYOUT

Status: Completed

Summary:

- Changed candidate-review K-line chart rendering to a local forward-adjusted display approximation by back-adjusting earlier OHLC values around large discontinuities in the unadjusted local daily K source.
- Kept raw source data unchanged and retained original open/close values in chart hover tooltips for traceability.
- Reduced K-line chart height and changed the candidate-review detail layout to a 1/3 left theme block plus 2/3 right trend/K-line block.
- Kept reason, risk, and source-event sections full-width below the theme/trend row.
- Preserved MVP6 boundaries: no network access, no new dependency, no JSON generation change, no watchlist write, no sync entry, and no trading workflow change.

## MVP6-003G-MA5-LAYOUT

Status: Completed

Summary:

- Added a MA5 line to the candidate-review inline K-line SVG chart, using the forward-adjusted display close prices.
- Increased the chart height to improve candlestick readability.
- Updated the theme/trend row to a 2/5 left theme block and 3/5 right trend/K-line block with aligned heights.
- Changed the lower candidate-review detail area into a 2x2 grid for selection reason, risk/observation, source events, and manual status.
- Preserved MVP6 boundaries: no network access, no new dependency, no JSON generation change, no watchlist write, no sync entry, and no trading workflow change.

## MVP6-SIDENAV-UX

Status: Completed

Summary:

- Reworked the side navigation into a full-height left hover zone with an inner sliding navigation panel.
- The expanded side panel now spans from page top to bottom and its right edge is calculated to meet the centered content area on wide screens.
- The nav remains expanded while the mouse stays inside the left-side hover zone, reducing accidental collapse when moving toward or clicking nav items.
- Preserved MVP6 boundaries: no network access, no new dependency, no JSON generation change, no watchlist write, no sync entry, and no trading workflow change.

## MVP6-SIDENAV-PERSISTENT

Status: Completed

Summary:

- Replaced the auto-hide side navigation with a persistent fixed left sidebar.
- Shifted the header and main content area to the right so the sidebar no longer overlays or cuts into the Dashboard content.
- Added a cleaner sidebar brand area, vertically stacked navigation buttons, and a small read-only/watchlist boundary footer.
- Removed the slide-in transform behavior and hidden vertical navigation tab from the desktop layout.
- Preserved MVP6 boundaries: no network access, no new dependency, no JSON generation change, no watchlist write, no sync entry, and no trading workflow change.

## MVP6-HEADER-CONTENT-WIDTH

Status: Completed

Summary:

- Removed the global top header because the persistent left sidebar now owns the Dashboard brand and navigation.
- Expanded the main content width to fill the remaining viewport area beside the left sidebar instead of using the previous centered max-width layout.
- Kept the page-specific hero headers as the primary context headers for each route.
- Preserved MVP6 boundaries: no network access, no new dependency, no JSON generation change, no watchlist write, no sync entry, and no trading workflow change.

## MVP6-004G-WEEKLY-K-PROBE

Status: Completed

Summary:

- Added `scripts/probes/test_weekly_k_probe.py` for real weekly K-line fetching from Tencent using `week` plus qfq/hfq adjustment parameters.
- The weekly probe outputs `data/market/weekly_k_latest.json` and dated `data/market/weekly_k_YYYYMMDD.json` files.
- Verified the weekly probe with `--limit 25 --weeks 80 --adjust-type qfq`; all 25 candidate rows returned OK.

## MVP6-004G-CANDIDATE-KLINE-TABS

Status: Completed

Summary:

- Updated `/candidate-watchlist` cards to use a left information panel and right chart panel.
- Added日K/周K切换 using local Dashboard JavaScript with no third-party dependencies.
- 日K reads `data/market/daily_k_latest.json`; 周K reads the new `data/market/weekly_k_latest.json`.
- Missing weekly data falls back to an inline empty-state message instead of failing page rendering.
- Preserved MVP6 boundaries: no new dependency, no JSON generation change, no watchlist write, no sync entry, and no trading workflow change.

## MVP6-004G-CANDIDATE-KLINE-COMPACT

Status: Completed

Summary:

- Tightened the `/candidate-watchlist` chart panel layout so the right-side K-line panel no longer stretches to match a taller left information panel.
- Kept the candidate-watchlist chart height in the recommended compact 220-240px range at 230px.
- Verified candidate-watchlist cards keep the left/right layout, Chinese field labels, and 日K/周K switching.
- Preserved MVP6 boundaries: no network access in this UI-only cleanup, no new dependency, no JSON generation change, no watchlist write, no sync entry, and no trading workflow change.

## MVP6-004G-KLINE-ALIGN-FIX

Status: Completed

Summary:

- Corrected the `/candidate-watchlist` chart layout after review: the right chart panel should align with the left information panel, while the chart itself should grow to fill the panel.
- Restored stretched left/right card alignment and changed the candidate-watchlist K-line chart to flexible height with a 300px minimum.
- Added 日K/周K switching to `/candidate-review` trend charts as well, using `daily_k_latest.json` and `weekly_k_latest.json`.
- Preserved MVP6 boundaries: no network access in this UI-only cleanup, no new dependency, no JSON generation change, no watchlist write, no sync entry, and no trading workflow change.
