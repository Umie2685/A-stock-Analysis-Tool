# MVP5-001G Candidate Filtering Audit

Generated: 2026-06-19

## 1. Scope

This audit initializes MVP5 candidate filtering work. It reviews the current candidate generation mechanism and adds user preference configuration for a future candidate review pool.

This task does not change candidate generation code, Dashboard code, watchlist content, network probes, or synchronization behavior.

## 2. Current Candidate Generation Chain

Current local chain:

```text
data/manual/hot_events_manual.json
+ data/evidence/fast_evidence_pack_latest.json
-> scripts/analysis/analyze_hot_events.py
-> data/analysis/hot_events_latest.json
-> scripts/analysis/build_candidate_watchlist.py
-> data/analysis/candidate_watchlist_latest.json
```

MVP4 then adds trend context:

```text
data/analysis/candidate_watchlist_latest.json
-> scripts/run_mvp4_pipeline.py
-> data/market/daily_k_latest.json
-> scripts/analysis/analyze_trends.py
-> data/analysis/trend_analysis_latest.json
```

The current candidate file reports `candidate_count=25`, `in_watchlist_count=1`, `not_in_watchlist_count=24`, `sort_rule=heat_score_desc`, and `score_rule=event strength weight + event count + relevance score`.

## 3. Current Scoring Mechanism

`scripts/analysis/build_candidate_watchlist.py` reads `hot_events_latest.json`, groups `related_stocks` by stock code, preserves enabled watchlist membership, then sorts candidates by descending `heat_score`, descending `event_count`, and ascending code.

Current constants:

```text
IMPACT_WEIGHT = {"high": 6, "medium": 3, "low": 1, "unknown": 0}
IMPACT_RANK = {"high": 3, "medium": 2, "low": 1, "unknown": 0}
```

Current formula:

```text
heat_score =
  sum(IMPACT_WEIGHT for each distinct event strength)
  + event_count * 2
  + relevance_score_max * 1.5
  + relevance_score_avg
```

Field notes:

- `heat_score`: participates in primary sorting.
- `event_count`: participates in score and tie-break sorting.
- `max_impact_strength`: derived from event strengths; displayed as the strongest linked event level.
- `relevance_score_max`: participates in score.
- `relevance_score_avg`: participates in score.
- `roles`: display and explanation field only.
- `reasons`: display and explanation field only.
- `risk_notes`: display and explanation field only.
- `in_watchlist`: display and membership context only; it does not affect sorting.
- `related_concepts`: display, grouping, and downstream context field; it does not directly add score in `build_candidate_watchlist.py`.
- `source_event_titles`: display and traceability field only.

## 4. How `concept_map.json` Affects Candidates

`scripts/analysis/analyze_hot_events.py` loads `config/concept_map.json`. For each hot-event input, it matches concept keywords and concept `related_stocks`. A stock can enter the candidate list only after it appears as a matched `related_stock` in a hot event.

Current concepts:

- AI算力
- 光通信
- PCB
- 数据中心
- 有色金属
- 消费电子
- 创新药
- 核电
- 商业航天
- 机器人
- 半导体国产替代
- 固态电池
- 低空经济
- 军工

Each concept affects candidates through:

- `keywords`: determines whether a hot event maps to the concept.
- `related_stocks`: determines which stocks can flow into `related_stocks` and later candidate buckets.
- `role`, `relevance_score`, `reason`, `risk_note`: explain stock links and influence relevance fields. `relevance_score` affects `heat_score`; the other fields explain context.

Potential mismatch with current user preferences:

- `机器人` currently can add candidates such as 688017, 002050, 002747, 300750, 002074, and 300073 through robot-related events. MVP5 preferences say this theme should not add preference score.
- `低空经济` is present and can add candidates such as 002085, 002179, 600118, and 002465, but MVP5 preferences mark it for downranking or exclusion.
- `创新药` and `消费电子` are present and can introduce names outside the stronger technology hardware and resource-material focus.
- `有色金属` currently mixes strategic resource logic with broader resource-cycle exposure, so it cannot yet separate technology-chain resources from traditional resource cyclicals.
- `商业航天` and `军工` can add useful hardware or connector names, but they also increase broader theme exposure without a user preference layer.

Potential coverage gaps:

- Strong preference themes are not represented one-to-one: AI硬件, 半导体设备, 半导体材料, 半导体新材料, 国产替代, 先进封装, PCB, 光模块, CPO, 高速铜缆, 连接器, 算力硬件, 存储, 服务器电源, and 液冷 are partly covered by AI算力, 光通信, PCB, 数据中心, and 半导体国产替代, but not separately scored.
- Resource watch themes such as 稀土, 小金属, 战略资源, 卡脖子材料, 先进制造上游, 半导体上游材料, 高端化工材料, and 化工产品 are mostly compressed into 有色金属, so finer preference handling is not available yet.
- Current concept links do not classify stock style as core leader, trend mid-cap anchor, elastic small-cap, or sentiment height marker.

## 5. Current Mechanism Limits

- It knows concept relevance, but not whether a candidate matches user preferences.
- It does not distinguish core leader, trend mid-cap anchor, elastic small-cap, or sentiment height marker.
- It does not separate strong-preference themes from blocked or downranked themes.
- It does not separate technology-chain resources from traditional old-cycle resources.
- `overheated` is currently treated as a risk state in trend analysis, while MVP5 should keep it available as a market-height observation label.
- Watchlist synchronization lacks a separate `candidate_review` pool for manual review.
- Current `watchlist.json` already contains auto-added candidate rows from previous work, but MVP5-001G does not modify or clean it.

## 6. MVP5 Recommended Refactor Plan

Recommended future chain:

```text
data/analysis/candidate_watchlist_latest.json
+ data/analysis/trend_analysis_latest.json
+ config/user_stock_preferences.json
-> data/analysis/candidate_review_latest.json
-> Dashboard candidate-review page
-> manual confirmation
-> optional watchlist synchronization
```

Future `candidate_review` should:

- Preserve original `candidate_watchlist` fields.
- Add preference theme matches and downrank reasons.
- Add trend-state context from `trend_analysis_latest.json`.
- Keep `overheated` as `market_height_watch` when configured.
- Split candidates into `core_midcap`, `elastic_sentiment`, and `trend_reserve` buckets.
- Respect `daily_review_limit=5` before any larger sector quota is introduced.
- Require manual confirmation before any watchlist update.

## 7. New User Preference Config

Added:

```text
config/user_stock_preferences.json
config/user_stock_preferences.example.json
```

Important initialized values:

- Strong themes: AI hardware, semiconductor equipment/materials, domestic substitution, advanced packaging, PCB, optical module/CPO, high-speed copper cable, connector, compute hardware, storage, server power, and liquid cooling.
- Watch themes: rare earth, minor metals, strategic resources, price-rise logic, constrained materials, advanced-manufacturing upstream, semiconductor upstream materials, high-end chemical materials, and chemical products.
- Neutral or disabled theme: robot.
- Downrank or block themes: medicine, consumption, property, finance, low-altitude economy, game/media game, traditional old-cycle stock, and pure concept speculation.
- Hard filters: exclude BJ market and ST; do not exclude new listing or overheated by default.
- `overheated_policy.mode=keep_as_market_height` with label `market_height_watch`.
- Daily review limit: 5.
- Initial quotas: `core_midcap=2`, `elastic_sentiment=2`, `trend_reserve=1`.
- Weights: hotspot 0.5, trend 0.5, preference 0.5, risk penalty 0.3.
- Watchlist sync: `manual_confirm`, `auto_sync_to_watchlist=false`.

## 8. Compliance Notes

MVP5-001G only adds documentation and configuration. It does not:

- Modify `scripts/analysis/build_candidate_watchlist.py`.
- Modify `scripts/analysis/analyze_hot_events.py`.
- Add a `candidate_review` generator.
- Change Dashboard routes or rendering.
- Change `config/watchlist.json`.
- Access network sources.
- Add runtime dependencies.
- Add automatic trading, order placement, or directional operation output.
