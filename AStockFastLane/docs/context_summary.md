# Context Summary

This document summarizes the current AStockFastLane MVP0 state for later development or `/compact` continuation.

## 1. Current Project Status

AStockFastLane has completed MVP0. The project can collect a small amount of public news and announcement metadata, normalize it into a Fast Evidence Pack, and generate a Markdown research-assistance report.

Current data chain:

```text
Eastmoney global news + CNInfo announcements -> Fast Evidence Pack -> Markdown report
```

The project remains a local data organization and research-assistance tool. It does not provide investment advice.

## 2. Completed Task IDs

- MVP0-001: Created project skeleton.
- MVP0-002: Reviewed a-stock-data reference material.
- MVP0-003: Implemented Eastmoney news minimal probe.
- MVP0-003S: Attempted and documented a-stock-data Skill installation and usage plan.
- MVP0-005G: Built initial Fast Evidence Pack from Eastmoney news.
- MVP0-006G: Generated initial Markdown report.
- MVP0-007G: Added CNInfo announcement minimal probe.
- MVP0-008G: Merged CNInfo announcements into Fast Evidence Pack.
- MVP0-009G+010G: Upgraded report for news + announcements and added one-click pipeline.
- MVP0-011G: Prepared MVP0 release notes, README update, and context summary.

## 3. Known Endpoints

Eastmoney global news endpoint:

```text
https://np-weblist.eastmoney.com/comm/web/getFastNewsList
```

Current probe parameters include:

```text
client=web
biz=web_724
fastColumn=102
pageSize=10
```

CNInfo announcement endpoint:

```text
https://www.cninfo.com.cn/new/hisAnnouncement/query
```

Current probe method:

```text
POST form request for one sample stock; metadata only; no PDF download.
```

## 4. Core Files

- `README.md`
- `scripts/run_mvp0_pipeline.py`
- `scripts/probes/test_eastmoney_news_probe.py`
- `scripts/probes/test_cninfo_announcement_probe.py`
- `scripts/pipeline/build_fast_evidence_pack.py`
- `scripts/pipeline/generate_fast_report.py`
- `scripts/check_project.py`
- `data/cache/eastmoney_news_probe_latest.json`
- `data/cache/cninfo_announcement_probe_latest.json`
- `data/evidence/fast_evidence_pack_latest.json`
- `reports/fast_report_latest.md`
- `docs/current_progress.md`
- `docs/endpoint_probe_results.md`
- `docs/mvp0_release_notes.md`

## 5. Development Boundaries

- Keep request volume small.
- Use explicit timeout values.
- Save raw/cache outputs for traceability.
- Do not add automatic trading.
- Do not write investment advice.
- Do not use high-frequency full-market crawling.
- Do not bypass access controls or anti-abuse protections.
- Do not add LLM, web page, or database layers until explicitly planned.
- Keep reports clearly labeled as data整理 and research assistance.

## 6. Next Plan

- MVP1-001G: 接入东财研报 probe
- MVP1-002G: 研报并入 Evidence Pack
- MVP1-003G: 报告支持新闻 + 公告 + 研报

## 7. Continuation Notes for Codex

When continuing after context compression:

- Treat `C:\Users\Administrator\Desktop\AStockFastLane\AStockFastLane` as the project root.
- Read `README.md`, `docs/current_progress.md`, `docs/endpoint_probe_results.md`, and this file first.
- Do not rerun probes unless the active task explicitly allows network access.
- For documentation-only tasks, run only `python scripts/check_project.py`.
- Preserve the no-investment-advice and no-automatic-trading boundaries.
