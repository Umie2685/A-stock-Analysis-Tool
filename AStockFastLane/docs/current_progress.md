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
