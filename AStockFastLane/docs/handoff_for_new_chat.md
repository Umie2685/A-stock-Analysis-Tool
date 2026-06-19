# Handoff for New Codex Chat

This is the standard handoff note for continuing AStockFastLane in a new Codex conversation.

## 1. Project Root

```text
C:\Users\Administrator\Desktop\AStockFastLane\AStockFastLane
```

In the new chat, ask Codex to read this file first, then read:

- `README.md`
- `docs/current_progress.md`
- `docs/mvp2_release_notes.md`
- `docs/endpoint_probe_results.md`
- `docs/mvp2_watchlist_report_notes.md`

## 2. Current Project Status

AStockFastLane is a local A-share public-information collection and research-assistance project.

Current sealed stage:

```text
MVP2 sealed
```

Current main capability:

```text
config/watchlist.json
-> watchlist-aware probes
-> Fast Evidence Pack
-> watchlist-grouped Markdown report
```

The project is not a trading system. It does not generate investment advice, trading advice, trading signals, orders, or return promises.

## 3. Current Entrypoints

Use these from the project root.

Offline report-only entry:

```bash
python scripts/run_offline_report.py
```

- Reads existing `data/evidence/fast_evidence_pack_latest.json`.
- Regenerates `reports/fast_report_latest.md`.
- Regenerates dated report such as `reports/fast_report_20260614.md`.
- Does not access the network.
- Does not run probes.

MVP1 compatibility refresh entry:

```bash
python scripts/run_mvp1_pipeline.py
```

- Refreshes news + announcements + research reports.
- Rebuilds the Fast Evidence Pack.
- Regenerates the Markdown report.
- Kept for compatibility.

MVP2 recommended refresh entry:

```bash
python scripts/run_mvp2_pipeline.py
```

- Checks `config/watchlist.json`.
- Refreshes Eastmoney news.
- Refreshes watchlist CNInfo announcement metadata.
- Refreshes watchlist Eastmoney research report metadata.
- Rebuilds the Fast Evidence Pack.
- Regenerates the watchlist-grouped Markdown report.

Watchlist validation entry:

```bash
python scripts/check_watchlist.py
```

Direct report generation entry:

```bash
python scripts/pipeline/generate_fast_report.py
```

## 4. Current Data Flow

```text
config/watchlist.json
-> scripts/check_watchlist.py
-> scripts/probes/test_eastmoney_news_probe.py
-> scripts/probes/test_cninfo_announcement_probe.py
-> scripts/probes/test_eastmoney_report_probe.py
-> data/cache/*_latest.json
-> data/raw/*_YYYYMMDD.json
-> scripts/pipeline/build_fast_evidence_pack.py
-> data/evidence/fast_evidence_pack_latest.json
-> data/evidence/fast_evidence_pack_YYYYMMDD.json
-> scripts/pipeline/generate_fast_report.py
-> reports/fast_report_latest.md
-> reports/fast_report_YYYYMMDD.md
```

News is displayed globally in the report.

Announcement and research report evidence are grouped by watchlist stock using:

```text
query_code / query_name / query_market
```

Fallback fields include:

```text
stock_code / stock_name / symbol / company
```

## 5. Current Watchlist

Main file:

```text
config/watchlist.json
```

Current default enabled symbol:

```text
688017 / 绿的谐波 / SH
```

Supported watchlist fields:

- `code`: six-digit A-share symbol.
- `name`: stock name.
- `market`: optional market label such as `SH`, `SZ`, or `BJ`.
- `enabled`: whether the symbol is included in probe batches.
- `orgId`: optional CNInfo organization id.
- `note`: optional human note.

Example file:

```text
config/watchlist.example.json
```

## 6. Completed MVP2 Capabilities

MVP2-001G:

- Added watchlist configuration.
- Added watchlist example file.
- Added standard-library watchlist loader and validator.
- Added `scripts/check_watchlist.py`.

MVP2-002G:

- Upgraded CNInfo announcement probe to read enabled watchlist symbols.
- Preserved `query_code`, `query_name`, `query_market`, and `query_orgId`.
- Does not download or parse announcement PDFs.

MVP2-003G:

- Upgraded Eastmoney research report probe to read enabled watchlist symbols.
- Preserved `query_code`, `query_name`, and `query_market`.
- Does not download report PDFs or parse full report text.
- Keeps rating / target price / institution opinion as source metadata only.

MVP2-004G:

- Upgraded Fast Evidence Pack generation to preserve watchlist query metadata.
- Kept evidence types as `news`, `announcement`, and `research_report`.

MVP2-005G:

- Upgraded Markdown report with `观察池个股证据`.
- Groups announcement and research_report items by stock.
- Keeps news as a global section.

MVP2-006G:

- Added `scripts/run_mvp2_pipeline.py`.
- Stops on first failed step.
- Prints latest evidence/report paths and item counts on success.

MVP2-007G:

- Updated README and progress docs for MVP2 entries and watchlist semantics.

MVP2-FINAL:

- Added `docs/mvp2_release_notes.md`.
- Updated this handoff document for new-chat continuation.

## 7. Current Outputs and Counts

Latest Evidence Pack:

```text
data/evidence/fast_evidence_pack_latest.json
```

Latest report:

```text
reports/fast_report_latest.md
```

Latest verified counts:

```text
news: 10
announcement: 10
research_report: 10
total: 30
```

Report contains:

- `## 4. 观察池个股证据`
- `### 4.1 688017 绿的谐波 SH`
- `#### 公告证据`
- `#### 研报证据`
- `## 5. 免责声明`

## 8. Development Boundaries

Preserve these boundaries unless the user explicitly changes the task:

- No investment advice.
- No trading advice.
- No trading signals.
- No automatic trading.
- No order placement.
- No return promises.
- No announcement PDF download.
- No research report PDF download.
- No PDF parsing.
- No LLM call from project runtime.
- No third-party dependency unless a future task explicitly allows it.
- No high-frequency crawling.
- No full-market crawling.
- No endpoint changes unless the task explicitly asks for endpoint work.
- Keep request volumes small and explicit.
- For no-network tasks, do not run probes or pipeline entries that run probes.

Forbidden investment-advice style phrases to avoid in generated reports or summaries:

```text
推荐买入
建议关注
投资机会
建议买入
建议增持
强烈推荐
收益承诺
稳赚
```

Important nuance:

- Source metadata may contain raw rating values such as `增持` or `买入`.
- These must remain clearly labeled as original source metadata.
- Do not rewrite them as project advice.

## 9. Current Git Status Guidance

The working tree is intentionally dirty from the staged MVP sequence. Do not revert user or historical changes.

Expected MVP2 source and documentation changes include:

- `README.md`
- `docs/current_progress.md`
- `docs/endpoint_probe_results.md`
- `docs/cninfo_watchlist_probe_notes.md`
- `docs/eastmoney_report_watchlist_probe_notes.md`
- `docs/fast_evidence_pack_watchlist_notes.md`
- `docs/mvp2_watchlist_report_notes.md`
- `docs/mvp2_release_notes.md`
- `docs/handoff_for_new_chat.md`
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

Generated runtime artifacts from validation runs include:

- `data/cache/*_latest.json`
- `data/raw/*_20260614.json`
- `data/evidence/fast_evidence_pack_latest.json`
- `data/evidence/fast_evidence_pack_20260614.json`
- `reports/fast_report_latest.md`
- `reports/fast_report_20260614.md`

Items to review separately before committing or packaging:

- `../tmp_stock_docs/`
- Any generated `data/` and `reports/` files that appear modified despite `.gitignore`.

## 10. Verification Commands

No-network checks:

```bash
python scripts/check_watchlist.py
python scripts/run_offline_report.py
python -m py_compile scripts/run_mvp2_pipeline.py scripts/pipeline/generate_fast_report.py scripts/utils/watchlist_loader.py
```

Network refresh check, only when the task permits network/probe execution:

```bash
python scripts/run_mvp2_pipeline.py
```

Report structure check:

```bash
rg -n "观察池个股证据|688017|绿的谐波|公告证据|研报证据|免责声明" reports/fast_report_latest.md
```

Investment-advice keyword check:

```bash
rg -n "推荐买入|建议关注|投资机会|建议买入|建议增持|强烈推荐|收益承诺|稳赚" reports/fast_report_latest.md
```

Expected result for the keyword check:

```text
no matches
```

## 11. Recommended MVP3 Starting Point

Do not begin MVP3 with a large feature.

Recommended first small MVP3 task:

```text
MVP3-001G: Add an offline pipeline state checker.
```

Suggested file:

```text
scripts/check_pipeline_state.py
```

Suggested behavior:

- Read `config/watchlist.json`.
- Check whether latest cache files exist.
- Check whether latest Evidence Pack exists.
- Check whether latest report exists.
- Print counts for news / announcement / research_report / total if available.
- Print whether report contains the expected watchlist grouped sections.
- Print whether no-advice keywords are absent.
- Do not access the network.
- Do not run probes.
- Do not modify files.
- Use Python standard library only.

Alternative small MVP3 tasks:

- Evidence Pack schema audit.
- Markdown report structure audit.
- `run_mvp2_pipeline.py --dry-run`.
- A small JSON summary file for local state, generated offline only.

Avoid at MVP3 start:

- Web UI.
- LLM integration.
- Large multi-stock crawling.
- PDF parsing.
- Investment scoring.
- Any trading signal workflow.

## 12. Suggested Prompt for New Chat

Copy this into the new Codex conversation:

```text
请继续开发 AStockFastLane。

项目路径：
C:\Users\Administrator\Desktop\AStockFastLane\AStockFastLane

请先阅读：
docs/handoff_for_new_chat.md
README.md
docs/current_progress.md
docs/mvp2_release_notes.md
docs/endpoint_probe_results.md

当前状态：MVP2 已封版。不要马上启动大规模 MVP3。

下一步请先做一个很小的 MVP3 起步任务：
MVP3-001G：新增离线 pipeline state checker。

严格边界：
1. 不访问网络；
2. 不运行 probe；
3. 不下载 PDF；
4. 不解析 PDF；
5. 不调用 LLM；
6. 不引入第三方依赖；
7. 不做投资建议；
8. 不修改现有 probe / evidence / report 生成逻辑；
9. 只使用 Python 标准库；
10. 优先新增 scripts/check_pipeline_state.py。
```
