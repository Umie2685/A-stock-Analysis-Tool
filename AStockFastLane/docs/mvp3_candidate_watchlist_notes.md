# MVP3-007G~010G Candidate Watchlist Notes

## Scope

This batch completes the local chain:

```text
hot event -> concept match -> candidate observation stocks -> Dashboard display
```

It remains fully offline. It does not access the network, run probes, download or parse PDFs, call an LLM, connect market data, or create trading output.

## Manual Hot Event Input

Manual hot events live at:

```text
data/manual/hot_events_manual.json
```

Example format:

```text
data/manual/hot_events_manual.example.json
```

Only items with `enabled: true` are analyzed. Manual items are normalized as:

```text
input_source: manual_hot_event
evidence_type: manual_hot_event
source: manual_hot_event
```

If the manual input file is missing, `analyze_hot_events.py` prints a warning and continues with Evidence Pack news.

## Concept Map

`config/concept_map.json` now covers:

```text
AI算力
光通信
PCB
数据中心
有色金属
消费电子
创新药
核电
商业航天
机器人
半导体国产替代
固态电池
低空经济
军工
```

Each concept includes keywords, transmission logic, typical triggers, risk notes, and related stocks.

`relevance_score` is a 1-5 concept relevance score only. It is not an investment value score.

## Candidate Watchlist Generator

Run from the project root:

```bash
python scripts/analysis/build_candidate_watchlist.py
```

Inputs:

```text
data/analysis/hot_events_latest.json
config/watchlist.json
```

Outputs:

```text
data/analysis/candidate_watchlist_latest.json
data/analysis/candidate_watchlist_YYYYMMDD.json
reports/candidate_watchlist_latest.md
reports/candidate_watchlist_YYYYMMDD.md
```

Aggregation rules:

- Collect `related_stocks` from hot events.
- Group by stock code.
- Merge related concepts, source hot events, roles, reasons, and risk notes.
- Mark whether the code is already in `config/watchlist.json`.
- Calculate `heat_score` from event strength, event count, and relevance scores.
- Sort by `heat_score` descending.

The output label is:

```text
candidate_watchlist
```

## Dashboard

The Dashboard now includes:

```text
/candidate-watchlist
```

The homepage also includes a candidate-watchlist overview and entry link.

The candidate page displays:

- Candidate count.
- In-watchlist count.
- Not-in-watchlist count.
- Candidate cards sorted by `heat_score`.
- Code, name, heat score, related concepts, source events, roles, reasons, risk notes, and watchlist status.

If the candidate output file is missing, the page shows a warning and does not crash.

## Boundary

Allowed wording:

```text
候选观察股
研究辅助
风险提示
不构成投资建议
```

Forbidden wording remains excluded from authored output:

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
