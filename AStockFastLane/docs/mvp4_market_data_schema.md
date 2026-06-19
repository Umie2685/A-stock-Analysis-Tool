# MVP4 Market Data Schema

## 1. MVP4 Data Goal

MVP4 starts from low-frequency daily K data because it fits the current AStockFastLane boundary: small watchlist, public information, local files, auditable output, and no trading automation. Daily K data is enough to describe recent trend context for candidate observation stocks without introducing order-book pressure, high-frequency crawling, or fragile realtime state.

The intended MVP4 chain is:

```text
data/analysis/candidate_watchlist_latest.json
-> limited daily K probe
-> data/market/daily_k_latest.json
-> simple trend context in a later MVP4 step
-> local Dashboard display in a later MVP4 step
```

MVP4-001G only defines the schema and probe plan. It does not implement a complex trend analyzer and does not change Dashboard pages.

## 2. Daily K Schema

Daily K output should be a JSON object with metadata plus an `items` array. Each `items[]` row represents one stock on one trade date.

| 字段名 | 类型 | 是否必需 | 含义 | 示例 |
| --- | --- | --- | --- | --- |
| `code` | string | 是 | 标准 6 位 A 股代码 | `601899` |
| `name` | string | 是 | 股票名称，优先来自候选池或 watchlist | `示例股票A` |
| `market` | string | 建议 | 市场标识 | `SH` |
| `trade_date` | string | 是 | 交易日期，格式 `YYYY-MM-DD`；失败时可为空 | `2026-06-18` |
| `open` | number/null | 是 | 开盘价 | `10.10` |
| `high` | number/null | 是 | 最高价 | `10.50` |
| `low` | number/null | 是 | 最低价 | `9.90` |
| `close` | number/null | 是 | 收盘价 | `10.30` |
| `volume` | number/null | 是 | 成交量，保留来源单位并在源说明中注明 | `12345600` |
| `amount` | number/null | 是 | 成交额，保留来源单位并在源说明中注明 | `126789000.0` |
| `pct_chg` | number/null | 是 | 当日涨跌幅百分比 | `1.98` |
| `turnover` | number/null | 建议 | 换手率百分比；来源无该字段时为 `null` | `2.35` |
| `source` | string | 是 | 数据来源或 fallback 路径 | `tencent_daily_k` |
| `adjust_type` | string | 建议 | 复权方式，先用 `none`、`qfq`、`hfq` 之一 | `none` |
| `query_code` | string | 建议 | 本次查询使用的代码 | `601899` |
| `query_name` | string | 建议 | 本次查询使用的名称 | `示例股票A` |
| `data_status` | string | 是 | 单条数据状态 | `ok` |
| `error_message` | string | 是 | 失败或异常说明，正常时为空字符串 | `` |
| `created_at` | string | 是 | 本条记录写入时间，ISO 8601 | `2026-06-19T00:00:00+08:00` |

### 2.1 Raw Market Fields

Raw market fields are the values directly describing daily trading data:

```text
open, high, low, close, volume, amount, pct_chg, turnover, trade_date
```

These fields should not contain derived trend judgments. If the provider uses different names or units, the probe should normalize field names while preserving provider notes in top-level metadata.

### 2.2 Normalized Fields

Normalized fields make downstream code stable across providers:

```text
code, name, market, query_code, query_name, source, adjust_type, data_status, error_message, created_at
```

`data_status` should be present even when a row failed, so the later analysis can distinguish "no row because code was skipped" from "row exists but fetch failed".

### 2.3 Future Trend-Analysis Derived Fields

Future MVP4 trend outputs should live outside daily K raw output. Suggested derived fields for `data/analysis/trend_analysis_latest.json`:

```text
trend_state
ma5
ma10
ma20
close_position_20d
volume_ratio_5d
drawdown_from_20d_high
rebound_from_20d_low
analysis_status
analysis_reason
```

These fields should not be written into the raw daily K file in MVP4-002G.

## 3. Output File Suggestions

MVP4-002G daily K probe outputs:

```text
data/market/daily_k_latest.json
data/market/daily_k_YYYYMMDD.json
```

MVP4-003G trend-analysis outputs:

```text
data/analysis/trend_analysis_latest.json
data/analysis/trend_analysis_YYYYMMDD.json
reports/trend_analysis_latest.md
reports/trend_analysis_YYYYMMDD.md
```

Recommended top-level daily K payload:

```json
{
  "schema_version": 1,
  "dataset": "daily_k",
  "generated_at": "2026-06-19T00:00:00+08:00",
  "source": "provider_name_or_latest_cache",
  "source_candidate_watchlist": "data/analysis/candidate_watchlist_latest.json",
  "adjust_type": "none",
  "limit": 20,
  "item_count": 0,
  "success_count": 0,
  "failure_count": 0,
  "items": [],
  "warnings": [],
  "disclaimer": "仅用于公开信息整理和研究辅助，不构成投资建议、交易建议或交易信号，不承诺任何回报。"
}
```

## 4. Data Quality Rules

Use row-level `data_status` plus top-level `warnings` instead of crashing the whole run whenever possible.

Recommended `data_status` values:

| 状态 | 含义 | 后续处理 |
| --- | --- | --- |
| `ok` | 成功取得可用日 K 数据 | 可进入后续趋势上下文分析 |
| `fetch_failed` | 网络、接口、解析或供应商返回异常 | 趋势状态应为 `unknown` |
| `insufficient_history` | 有数据但历史长度不足 | 趋势状态应为 `unknown` |
| `suspended` | 停牌或当日无有效成交 | 趋势状态应为 `unknown` |
| `zero_volume` | 成交量为 0 或缺失 | 趋势状态应为 `unknown` |
| `new_listing` | 上市时间过短，均线窗口不足 | 趋势状态应为 `unknown` |
| `fallback_cache` | 使用本地旧缓存或样例 fallback | 可展示来源，但趋势状态默认 `unknown`，除非后续明确允许缓存分析 |

Failure handling rules:

- Market fetch failure: write one row per failed candidate with `data_status: "fetch_failed"` and a concise `error_message`.
- Insufficient data: if available history is below the minimum window needed by the later rule, write `insufficient_history`.
- Suspended stocks: if provider marks suspended, or price fields are empty while the stock exists, write `suspended`.
- Zero-volume days: if `volume` is 0 or missing while price fields look stale, write `zero_volume`.
- Newly listed stocks: if history length is below the selected MA window, write `new_listing`.
- Source tracking: `source` must identify provider or fallback path, for example `tencent_daily_k`, `sina_daily_k`, `latest_cache`, or `example`.

## 5. Future Trend State Enum

MVP4-001G only defines direction. Exact numeric thresholds should be implemented and tested in a later task.

| trend_state | 含义 | 规则方向 |
| --- | --- | --- |
| `strong_uptrend` | 趋势强，收盘价处于短中期均线上方且量能配合 | close above MA5/MA10/MA20, recent highs improving, volume not shrinking sharply |
| `recovering` | 从低位修复，已有反弹但还未确认强趋势 | close back above MA5/MA10, rebound from recent low, MA20 still flat or above price |
| `sideways` | 横盘震荡，价格围绕均线窄幅波动 | close near MA10/MA20, volatility and volume moderate |
| `weakening` | 趋势转弱，跌破短期均线或回撤扩大 | close below MA5/MA10, drawdown from recent high increasing |
| `overheated` | 短期涨幅和量能过热，需要风险提示 | close far above MA5/MA20, volume spike, short-term pct change unusually high |
| `unknown` | 数据不足或质量不可信 | fetch failure, insufficient history, suspended, zero volume, new listing, malformed data |

## 6. MVP4-002G Minimal Probe Plan

Inputs:

```text
data/analysis/candidate_watchlist_latest.json
config/watchlist.json
```

Recommended scope:

- Read candidate stocks sorted by `heat_score`.
- Limit the first probe to the top 5-20 candidates.
- Preserve `code`, `name`, `in_watchlist`, and `heat_score` in probe metadata if useful.
- Prefer one low-frequency daily K source first.
- Use short timeouts and small request volume.
- Write latest plus dated JSON outputs.
- Keep all failures in structured rows rather than stopping after the first failed stock.

Suggested command for MVP4-002G:

```bash
python scripts/probes/test_daily_k_probe.py
```

The command name is a proposal only. It should not be added until MVP4-002G.

## 7. Boundaries

MVP4 market data is for public-information organization and research assistance only.

Do not add:

- automatic trading;
- order placement;
- trading signals;
- realtime order-book data;
- high-frequency crawling;
- large third-party dependencies;
- announcement or research-report PDF download;
- PDF parsing;
- LLM calls from project runtime;
- return promises.

MVP4-001G also does not change existing MVP0-MVP3 entrypoints and does not change Dashboard pages.
