# AStockFastLane MVP6 New Chat Handoff

Generated: 2026-06-20T00:15:00+08:00

## 1. Project Root

```text
C:\Users\Administrator\Desktop\AStockFastLane\AStockFastLane
```

## 2. Project Positioning

AStockFastLane is a local A-share public-information research console.

It is intended for:

- local public-information aggregation,
- rule-based hot-event and candidate-pool analysis,
- manual review workflow support,
- after-close research summary display.

Hard boundaries:

- No automatic trading.
- No automatic writing to `config/watchlist.json`.
- No watchlist sync unless a later task explicitly asks for a manually confirmed gate.
- No trading instruction wording.
- No third-party frontend framework.
- No network access unless a task explicitly allows an existing pipeline refresh.

## 3. Completed State

### MVP0 to MVP4

- MVP0/MVP1/MVP2 established the local evidence and watchlist reporting base.
- MVP3 added hot-event analysis, `candidate_watchlist`, and Dashboard pages.
- MVP4 added daily K based short-term trend analysis and trend Dashboard pages.

### MVP5

MVP5 completed the candidate-review and after-close-report loop:

```text
hot_events
-> candidate_watchlist
-> trend_analysis
-> candidate_review
-> candidate_review_status
-> daily_after_close_report
-> Dashboard
```

Key MVP5 files:

```text
config/user_stock_preferences.json
config/user_stock_preferences.example.json
scripts/analysis/build_candidate_review.py
scripts/manual/update_candidate_review_status.py
scripts/reports/build_daily_after_close_report.py
data/manual/candidate_review_status.json
data/manual/candidate_review_status.example.json
data/analysis/candidate_review_latest.json
reports/candidate_review_latest.md
data/analysis/daily_after_close_report_latest.json
reports/daily_after_close_report_latest.md
```

Important concept names:

- `watchlist`: long-term manual observation pool.
- `candidate_watchlist`: hot-event candidate pool. In Dashboard copy this should be shown as "热点候选池".
- `candidate_review`: user-preference filtered candidate review pool.
- `candidate_review_status`: local manual review status file.

### MVP6

MVP6 has started. It is a Dashboard/productization phase, not a new data-capability phase.

Completed:

- `MVP6-001G`: Dashboard UI Foundation + research-console homepage.
- `MVP6-001G-CLEANUP`: removed duplicate render functions and old UI remnants from `scripts/run_web_dashboard.py`.

The Dashboard is still a single-file standard-library HTTP server.

## 4. Current Dashboard Entry Point

Start local Dashboard:

```powershell
cd C:\Users\Administrator\Desktop\AStockFastLane\AStockFastLane
python scripts/run_web_dashboard.py --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/
```

Current core routes:

```text
/
/daily-report
/daily-report-report
/candidate-review
/candidate-review-report
/candidate-watchlist
/trend-analysis
/trend-analysis-report
/hot-events
/hot-events-report
/fast-report
```

## 5. Current Dashboard Structure

Main file:

```text
scripts/run_web_dashboard.py
```

The MVP6 UI foundation currently includes:

- `render_page_header(...)`
- one final `render_page(...)`
- one final `render_home(...)`
- one final `render_candidate_watchlist(...)`
- one final `render_candidate_watchlist_page(...)`
- cards/panels/badges/pills/detail grids/warnings/disclaimers/responsive CSS
- navigation order:

```text
首页
盘后报告
候选审核池
热点候选池
短期趋势分析
热点分析
热点报告
Fast Report
```

Homepage layout:

```text
研究控制台
今日关键结论
盘后报告摘要
候选审核池重点名单
今日热点主线
数据健康与更新时间
```

Important cleanup note:

- The duplicate `render_*` definitions from MVP6-001G were removed.
- `display_text()` was removed.
- A narrow `normalize_legacy_candidate_terms(...)` remains only to normalize historical generated Markdown or hot-event text when displayed. It should not be used as a general UI-copy crutch.

## 6. Verification Snapshot

Last verified in this chat:

```powershell
python -m py_compile scripts/run_web_dashboard.py
```

Result:

```text
PASS
```

HTTP check used a temporary local server and confirmed `200` for:

```text
/
/daily-report
/candidate-review
/candidate-watchlist
/trend-analysis
/hot-events
/hot-events-report
/fast-report
```

Visible-page checks confirmed:

- Homepage shows `研究控制台`.
- Dashboard shows `热点候选池`.
- Old visible copy `候选观察股` was not present.
- No `加入观察池` or `确认同步` button was present.

## 7. Known Dirty Workspace Notes

There are pre-existing dirty/untracked files from prior MVP work and local generated artifacts.

Known important note:

- `config/watchlist.json` may appear modified in `git status`, but MVP6 UI tasks did not modify it.
- Do not revert user or prior-task changes unless the user explicitly asks.
- Do not run `git add` or `git commit` unless explicitly requested.

Useful status command:

```powershell
git status --short
```

## 8. Boundaries For Next MVP6 Tasks

Default boundaries unless the user says otherwise:

- Modify mainly `scripts/run_web_dashboard.py`.
- Optionally update `docs/current_progress.md`.
- Do not modify JSON generation scripts for UI-only tasks:
  - `scripts/analysis/build_candidate_review.py`
  - `scripts/analysis/build_candidate_watchlist.py`
  - `scripts/analysis/analyze_hot_events.py`
  - `scripts/analysis/analyze_trends.py`
  - `scripts/reports/build_daily_after_close_report.py`
- Do not write `config/watchlist.json`.
- Do not add automatic sync entries.
- Do not add "加入观察池" or "确认同步" buttons unless a later task explicitly defines a safe manual-confirm workflow.
- Do not add network or dependencies for UI cleanup/refinement.

## 9. Suggested Next Task

Recommended next small task:

```text
MVP6-002G: Dashboard page-level ergonomics polish.
```

Scope suggestion:

- Keep data generation untouched.
- Refine `/daily-report` and `/candidate-review` for daily review ergonomics.
- Add only read-only UI helpers such as:
  - section anchors,
  - compact/expanded visual grouping,
  - clearer status badges,
  - no-write client-side filtering by status or bucket if implemented with plain HTML/CSS/vanilla JS.

Avoid:

- writing status files from Dashboard,
- syncing to watchlist,
- changing report/candidate generation logic.

## 10. Copy-Paste Prompt For New Chat

```text
继续 AStockFastLane MVP6 开发。

项目路径：
C:\Users\Administrator\Desktop\AStockFastLane\AStockFastLane

请先阅读：
docs/handoff_for_mvp6_new_chat.md
docs/current_progress.md

当前阶段：
MVP5 已完成，MVP6 已完成 MVP6-001G 和 MVP6-001G-CLEANUP。
Dashboard 主文件是 scripts/run_web_dashboard.py。

请继续做 MVP6 的小步 UI / 研究控制台优化任务。
默认边界：
- 不访问网络
- 不新增依赖
- 不修改 JSON 生成逻辑
- 不写 config/watchlist.json
- 不新增自动同步 watchlist
- 不新增交易建议
- 不做 git add / commit

优先保持 Dashboard 当前可见效果和概念命名：
- watchlist = 长期人工观察池
- candidate_watchlist = 热点候选池
- candidate_review = 候选审核池
```

