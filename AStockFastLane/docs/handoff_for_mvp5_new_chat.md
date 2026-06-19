# AStockFastLane MVP5 New Chat Handoff

Generated: 2026-06-19T18:15:01+08:00

## 1. Project Root

```text
C:\Users\Administrator\Desktop\AStockFastLane\AStockFastLane
```

## 2. Project Positioning

AStockFastLane is a local A-share hot-event capture and research-assistance system.

Boundaries:

- It organizes public information and local rule-based analysis.
- It does not run automatic trading.
- It does not promise returns.
- It does not output mandatory trading instructions.
- It does not connect order-book, intraday, or high-frequency data.

## 3. Completed Stages

- MVP0: Basic local project and data-flow foundation.
- MVP1: News, announcement, and research-report Evidence Pack chain.
- MVP2: Watchlist observation pool and public-information refresh pipeline.
- MVP3: Hot-event analysis, candidate watchlist generation, and local Dashboard pages.
- MVP4: Low-frequency daily K data, short-term rule-based trend analysis, Dashboard trend pages, and one-click MVP4 pipeline.

## 4. Current MVP4 Entry Points

Run the MVP4 generation chain:

```bash
python scripts/run_mvp4_pipeline.py --limit 20
```

Start the local Dashboard:

```bash
python scripts/run_web_dashboard.py
```

Dashboard pages:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/trend-analysis
http://127.0.0.1:8000/trend-analysis-report
http://127.0.0.1:8000/candidate-watchlist
http://127.0.0.1:8000/hot-events-report
```

## 5. Current MVP4 Data Flow

```text
data/analysis/candidate_watchlist_latest.json
-> scripts/run_mvp4_pipeline.py
-> scripts/probes/test_daily_k_probe.py
-> data/market/daily_k_latest.json
-> scripts/analysis/analyze_trends.py
-> data/analysis/trend_analysis_latest.json
-> reports/trend_analysis_latest.md
-> scripts/run_web_dashboard.py
-> /trend-analysis
```

## 6. Core MVP4 Outputs

```text
data/market/daily_k_latest.json
data/analysis/trend_analysis_latest.json
reports/trend_analysis_latest.md
```

The latest MVP4-006G audit run used:

```bash
python scripts/run_mvp4_pipeline.py --limit 20
```

Latest audit summary:

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

## 7. Known MVP4 Limits

1. Tencent daily K `amount`, `pct_chg`, and `turnover` may be `null`.
2. Current close-change metrics are derived in the trend-analysis layer from `close`.
3. `volume` is used for relative volume comparison only; it is not interpreted as absolute share turnover.
4. MVP4 has no realtime order-book, intraday, or high-frequency module.
5. Trend analysis is `rule_based` and only supports research assistance.
6. Network-source changes may cause daily K probe failures.
7. The latest daily K bar can lag the current calendar date.

## 8. Candidate Directions For MVP5

These are directions only. Do not implement them automatically.

- Direction A: Market-data quality enhancement and fallback sources.
- Direction B: After-market report automation.
- Direction C: Financial-report and research-report summary integration.
- Direction D: Hot-event persistence scoring.
- Direction E: Candidate watchlist layering: core, elastic, and risk-observation groups.
- Direction F: Research-report email delivery, limited to report sending and not trading alerts.

## 9. Suggested New Chat Opening

```text
Please continue AStockFastLane from MVP5.

Project root:
C:\Users\Administrator\Desktop\AStockFastLane\AStockFastLane

Read docs/handoff_for_mvp5_new_chat.md first, then inspect docs/current_progress.md and docs/endpoint_probe_results.md.

Current sealed state:
MVP0/MVP1/MVP2 sealed.
MVP3 completed.
MVP4 completed and audited through MVP4-006G.

Current MVP4 entry:
python scripts/run_mvp4_pipeline.py --limit 20
python scripts/run_web_dashboard.py

Current Dashboard pages:
/
/trend-analysis
/trend-analysis-report
/candidate-watchlist
/hot-events-report

For MVP5, start with a small planning step only. Do not add new data sources, realtime order-book, intraday, high-frequency, automatic trading, or trading instructions unless a specific MVP5 task says so.
```

