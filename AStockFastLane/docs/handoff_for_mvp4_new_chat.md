# Handoff for MVP4 New Codex Chat

This handoff is for starting MVP4 work in a new Codex conversation.

## 1. Project Root

```text
C:\Users\Administrator\Desktop\AStockFastLane\AStockFastLane
```

In the new chat, ask Codex to read this file first, then inspect the current project files listed in the MVP4-001G task.

## 2. Current Project Status

AStockFastLane is a local A-share public-information collection and research-assistance project.

Current sealed stages:

```text
MVP0 / MVP1 / MVP2 sealed
MVP3 completed
```

MVP3 completed the local hot-event research chain:

```text
Evidence Pack news + manual hot events
-> rule-based hot event analysis
-> concept matching
-> candidate watchlist generation
-> local Dashboard display
```

Current important outputs:

```text
data/analysis/hot_events_latest.json
reports/hot_events_latest.md
data/analysis/candidate_watchlist_latest.json
reports/candidate_watchlist_latest.md
```

The project is not a trading system. It must not generate buy/sell instructions, trading signals, automatic orders, or return promises.

## 3. Current MVP3 Entrypoints

Use these from the project root.

Watchlist validation:

```bash
python scripts/check_watchlist.py
```

Network refresh entry, only when the task explicitly permits network/probe execution:

```bash
python scripts/run_mvp2_pipeline.py
```

Offline hot-event analysis:

```bash
python scripts/analysis/analyze_hot_events.py
```

Offline candidate watchlist generation:

```bash
python scripts/analysis/build_candidate_watchlist.py
```

Local Dashboard:

```bash
python scripts/run_web_dashboard.py
```

Dashboard URLs:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/hot-events
http://127.0.0.1:8000/hot-events-report
http://127.0.0.1:8000/candidate-watchlist
http://127.0.0.1:8000/fast-report
```

## 4. Current Data Flow

MVP2 public information refresh:

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
-> scripts/pipeline/generate_fast_report.py
-> reports/fast_report_latest.md
```

MVP3 hot-event and candidate chain:

```text
data/evidence/fast_evidence_pack_latest.json
data/manual/hot_events_manual.json
config/concept_map.json
-> scripts/analysis/analyze_hot_events.py
-> data/analysis/hot_events_latest.json
-> reports/hot_events_latest.md
-> scripts/analysis/build_candidate_watchlist.py
-> data/analysis/candidate_watchlist_latest.json
-> reports/candidate_watchlist_latest.md
-> scripts/run_web_dashboard.py
```

Latest verified refreshed counts from the most recent run:

```text
news: 10
announcement: 10
research_report: 10
total evidence: 30
hot events: 14
manual_hot_event: 4
evidence_news: 10
candidate watchlist: 25
in watchlist: 1
not in watchlist: 24
```

Latest matched concepts from the refreshed MVP3 run:

```text
有色金属
AI算力
光通信
数据中心
机器人
固态电池
商业航天
低空经济
军工
```

## 5. Current Important Files to Inspect for MVP4-001G

The MVP4-001G task should start by reading these files and reporting if any are missing:

```text
config/watchlist.json
config/concept_map.json
data/analysis/candidate_watchlist_latest.json
scripts/analysis/analyze_hot_events.py
scripts/analysis/build_candidate_watchlist.py
scripts/run_web_dashboard.py
docs/current_progress.md
```

Do not assume the file contents. Inspect the current worktree as authoritative.

## 6. MVP4 Direction

MVP4 goal:

```text
候选观察股
-> 获取低频行情数据
-> 日 K / 成交量 / 涨跌幅 / 均线 / 放量 / 回撤
-> 判断短期趋势状态
-> Dashboard 展示
```

MVP4 should start cautiously with low-frequency daily K data. Do not jump into realtime order-book, high-frequency data, or trading automation.

## 7. MVP4-001G Task for New Chat

Task name:

```text
MVP4-001G: 低频行情数据 Schema 与个股日 K Probe 规划
```

Task objective:

```text
行情数据源调研 + 个股日 K 数据 schema 设计 + 最小落地方案
```

This is primarily a planning and schema-design task, not a large implementation task.

Required new document:

```text
docs/mvp4_market_data_schema.md
```

Allowed additions:

```text
data/market/.gitkeep
docs/mvp4_market_data_schema.md
```

Optional addition:

```text
data/market/daily_k_latest.example.json
```

If adding the example JSON, keep it small with only 1-2 stock examples.

## 8. Required Contents for docs/mvp4_market_data_schema.md

The document should include at least these sections.

### 8.1 MVP4 Data Goal

Explain why MVP4 starts with daily K / low-frequency market data instead of order-book or high-frequency data.

### 8.2 Daily K Schema

Recommended fields:

```text
code
name
trade_date
open
high
low
close
volume
amount
pct_chg
turnover
source
```

Useful supplemental fields:

```text
market
adjust_type
query_code
query_name
data_status
error_message
created_at
```

The document should distinguish:

- Raw market fields.
- Normalized fields.
- Future trend-analysis derived fields.

### 8.3 Output File Suggestions

Suggested MVP4-002G daily K outputs:

```text
data/market/daily_k_latest.json
data/market/daily_k_YYYYMMDD.json
```

Suggested MVP4-003G trend-analysis outputs:

```text
data/analysis/trend_analysis_latest.json
data/analysis/trend_analysis_YYYYMMDD.json
reports/trend_analysis_latest.md
reports/trend_analysis_YYYYMMDD.md
```

### 8.4 Data Quality Rules

Must explain:

- How market fetch failure is marked.
- How insufficient data is marked.
- How suspended stocks, zero-volume days, and newly listed stocks are handled.
- What should trigger `unknown` in trend analysis.
- How `source` records the data provider or fallback path.

### 8.5 Future Trend State Enum

Define and explain:

```text
strong_uptrend
recovering
sideways
weakening
overheated
unknown
```

Only define rule direction in MVP4-001G. Do not implement a complex trend analyzer yet.

## 9. Strict Boundaries for MVP4-001G

Do not do these in MVP4-001G:

```text
1. No automatic trading.
2. No buy / sell advice.
3. No realtime order-book.
4. No high-frequency data.
5. Do not directly modify Dashboard pages.
6. Do not directly implement a complex trend analyzer.
7. Do not introduce large third-party dependencies.
8. Do not break MVP0-MVP3 existing entrypoints.
```

Also preserve existing project-wide boundaries:

- No announcement PDF download.
- No research report PDF download.
- No PDF parsing.
- No LLM call from project runtime.
- No investment advice.
- No trading advice.
- No trading signals.
- No return promises.

Forbidden investment-advice wording in project-authored reports and pages:

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

Allowed wording:

```text
候选观察股
研究辅助
风险提示
不构成投资建议
```

## 10. MVP4-001G Self-Test Expectations

Even if MVP4-001G is documentation-only, run at least:

```bash
python -m py_compile scripts/analysis/analyze_hot_events.py
python -m py_compile scripts/analysis/build_candidate_watchlist.py
python -m py_compile scripts/run_web_dashboard.py
```

If any file is missing, report it explicitly instead of assuming it exists.

## 11. MVP4-001G Expected Final Reply Format

The new chat should reply with:

```text
1. 本次任务结论
2. 修改 / 新增文件
3. schema 设计摘要
4. 数据质量与 unknown 规则
5. 后续 MVP4-002G 建议
6. 自测结果
7. 风险与注意事项
```

Schema summary should include a table:

```text
字段名 / 类型 / 是否必需 / 含义 / 示例
```

MVP4-002G suggestions should cover:

```text
输入文件
输出文件
候选股数量限制
数据源优先级
失败容错方式
运行命令建议
```

## 12. Suggested Prompt for the New Chat

Copy this into the new Codex conversation:

```text
请继续开发 AStockFastLane。
项目路径：
C:\Users\Administrator\Desktop\AStockFastLane\AStockFastLane

请先阅读：
docs/handoff_for_mvp4_new_chat.md

然后执行 MVP4-001G：
低频行情数据 Schema 与个股日 K Probe 规划。

本次不是大规模开发任务，重点是：
1. 检查现有项目结构；
2. 新增 docs/mvp4_market_data_schema.md；
3. 设计日 K schema、输出文件、数据质量规则和趋势状态枚举；
4. 可选新增 data/market/.gitkeep 和 data/market/daily_k_latest.example.json；
5. 不改 Dashboard；
6. 不实现复杂趋势分析；
7. 不做自动交易；
8. 不输出买入/卖出建议；
9. 不引入大型第三方依赖。

请按任务书格式汇报：
1. 本次任务结论
2. 修改 / 新增文件
3. schema 设计摘要
4. 数据质量与 unknown 规则
5. 后续 MVP4-002G 建议
6. 自测结果
7. 风险与注意事项
```

