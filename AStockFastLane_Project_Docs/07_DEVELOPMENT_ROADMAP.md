# 07_DEVELOPMENT_ROADMAP：开发路线图

## MVP-0：最小端到端工具

目标：跑通从数据抓取到报告生成的完整闭环。

```text
新闻 probe
公告 probe
研报 probe
行情 probe
Evidence Pack
Markdown 报告
一键运行脚本
```

### MVP0-001：项目骨架初始化

产出：目录、README、requirements、current_progress。

### MVP0-002：接入 a-stock-data 参考材料

产出：本地记录 README / SKILL.md 来源、许可和可参考端点。

### MVP0-003：东财新闻 probe

产出：新闻 raw/cache JSON 和文档。

### MVP0-004：巨潮公告 probe

产出：公告 raw/cache JSON 和文档。

### MVP0-005：东财研报 probe

产出：研报 raw/cache JSON 和文档。

### MVP0-006：行情快照 probe

产出：行情 raw/cache JSON。

### MVP0-007：关联规则

产出：基于股票代码、公司名、关键词的简化关联函数。

### MVP0-008：Fast Evidence Pack

产出：`data/evidence/fast_evidence_pack_latest.json`。

### MVP0-009：Markdown 报告

产出：`reports/fastlane_report_YYYYMMDD.md`。

### MVP0-010：一键运行脚本

产出：`scripts/run_fastlane_pipeline.py`。

## MVP-1：质量提升

- provider 标准化；
- 字段单位说明；
- 多源交叉验证；
- LLM 报告润色；
- 缓存降级；
- 错误重试；
- watchlist 支持；
- 主题归因。

## MVP-2：产品化

- Streamlit 页面；
- 定时任务；
- 历史数据归档；
- 报告对比；
- 多策略模板；
- 用户自定义关键词。

## 永不纳入

- 自动交易；
- 券商账户连接；
- 实盘下单；
- 投资承诺；
- 绕过付费或鉴权数据。
