# 09_CODEX_TASKS_MVP0：可直接发给 Codex 的任务清单

下面任务按顺序执行。每次只发一个任务给 Codex。

---

## MVP0-001：初始化 AStockFastLane 项目骨架

任务编号：MVP0-001

任务名称：初始化 AStockFastLane 项目骨架

背景：
新项目以 a-stock-data 为核心参考，快速开发 A 股热点分析工具。当前是空项目，需要先创建目录结构、基础文档和最小运行环境。

目标：
创建项目骨架，不接入任何外部数据源。

允许新增文件：

- `README.md`
- `requirements.txt`
- `.gitignore`
- `scripts/probes/.gitkeep`
- `scripts/providers/.gitkeep`
- `scripts/packs/.gitkeep`
- `scripts/reports/.gitkeep`
- `scripts/utils/.gitkeep`
- `data/raw/.gitkeep`
- `data/cache/.gitkeep`
- `data/evidence/.gitkeep`
- `data/manual/watchlist_symbols.txt`
- `data/manual/keyword_topics.json`
- `reports/.gitkeep`
- `docs/current_progress.md`
- `docs/architecture.md`
- `docs/data_source_notes.md`

禁止行为：

- 不接入 a-stock-data 代码。
- 不请求外网。
- 不写爬虫。
- 不接 LLM。
- 不建数据库。
- 不做自动交易。

requirements 初始建议：

```text
requests
pandas
```

运行方式：

```bash
python --version
```

交付格式：

```text
1. 修改了哪些文件
2. 目录结构
3. requirements 内容
4. current_progress.md 写了什么
5. 是否请求了外网
6. 下一步建议
```

验收标准：

- 项目结构清晰；
- 没有网络请求；
- 没有业务代码；
- 文档说明项目边界。

---

## MVP0-002：接入 a-stock-data 参考材料审查记录

任务编号：MVP0-002

任务名称：记录 a-stock-data 参考材料与许可风险

目标：
下载或阅读 a-stock-data 的 README.md 和 SKILL.md，形成本项目的数据源参考文档。只做审查，不复制整包代码。

允许新增 / 修改：

- 新增 `docs/a_stock_data_reference.md`
- 修改 `docs/current_progress.md`

禁止修改：

- `scripts/*`
- `data/*`
- `reports/*`

要求：

记录以下内容：

- 项目来源 URL；
- README / SKILL.md 阅读时间；
- 覆盖的数据层；
- 适合 MVP-0 的端点；
- 暂缓端点；
- 许可 / attribution 情况；
- 不整包复制原则。

交付格式：

```text
1. 修改了哪些文件
2. 是否阅读 README / SKILL.md
3. 覆盖哪些数据层
4. MVP-0 优先哪些端点
5. 哪些端点暂缓
6. 是否复制了第三方代码
7. 下一步建议
```

---

## MVP0-003：东财新闻最小探针

任务编号：MVP0-003

任务名称：实现东财新闻最小 probe

背景：
需要优先验证新闻数据源能否用于自动热点分析。

目标：
参考 a-stock-data 中东财新闻 / 全球资讯 endpoint 的思路，实现本项目独立新闻 probe。

允许新增 / 修改：

- 新增 `scripts/providers/eastmoney_news_provider.py`
- 新增 `scripts/probes/test_eastmoney_news_probe.py`
- 新增 `docs/probe_eastmoney_news.md`
- 修改 `docs/current_progress.md`

输出文件：

- `data/raw/eastmoney_news_probe_YYYYMMDD.json`
- `data/cache/eastmoney_news_latest.json`

禁止行为：

- 不整包复制 a-stock-data。
- 不高频循环。
- 不并发。
- 不接 LLM。
- 不写 Evidence Pack。
- 不生成报告。

provider 返回结构建议：

```python
{
    "ok": True,
    "source": "eastmoney",
    "endpoint": "",
    "rows": 0,
    "items": [],
    "error_type": None,
    "error_message": None,
}
```

新闻 item 建议字段：

```json
{
  "title": "",
  "url": "",
  "publish_time": "",
  "source": "",
  "summary": "",
  "raw": {}
}
```

运行方式：

```bash
python scripts/probes/test_eastmoney_news_probe.py
```

交付格式：

```text
1. 修改了哪些文件
2. 如何运行
3. 请求了哪些 endpoint
4. 成功返回多少条
5. 字段有哪些
6. 生成了哪些 JSON
7. 哪些失败
8. 是否建议进入 provider 稳定封装
9. 下一步建议
```

验收标准：

- 单次最多抓 20 条；
- 有 timeout；
- 失败不崩溃；
- 生成 raw/cache JSON；
- 文档记录数据质量限制。

---

## MVP0-004：巨潮公告最小探针

任务编号：MVP0-004

任务名称：实现巨潮公告最小 probe

目标：
参考 a-stock-data 中巨潮公告 endpoint，验证是否能抓取少量公告列表。

允许新增 / 修改：

- 新增 `scripts/providers/cninfo_announcement_provider.py`
- 新增 `scripts/probes/test_cninfo_announcement_probe.py`
- 新增 `docs/probe_cninfo_announcement.md`
- 修改 `docs/current_progress.md`

输出文件：

- `data/raw/cninfo_announcement_probe_YYYYMMDD.json`
- `data/cache/cninfo_announcement_latest.json`

测试范围：

- 先用少量股票或关键词；
- 不下载 PDF 正文；
- 只抓列表和公告链接。

运行方式：

```bash
python scripts/probes/test_cninfo_announcement_probe.py
```

验收标准：

- 返回公告标题、公司、代码、时间、链接；
- 有 timeout；
- 失败不崩溃；
- 不接 Evidence Pack。

---

## MVP0-005：东财研报最小探针

任务编号：MVP0-005

任务名称：实现东财研报最小 probe

目标：
参考 a-stock-data 中东财研报 endpoint，验证研报列表 / 摘要可用性。

允许新增 / 修改：

- 新增 `scripts/providers/eastmoney_report_provider.py`
- 新增 `scripts/probes/test_eastmoney_report_probe.py`
- 新增 `docs/probe_eastmoney_report.md`
- 修改 `docs/current_progress.md`

输出文件：

- `data/raw/eastmoney_report_probe_YYYYMMDD.json`
- `data/cache/eastmoney_report_latest.json`

运行方式：

```bash
python scripts/probes/test_eastmoney_report_probe.py
```

验收标准：

- 返回研报标题、机构、时间、相关股票、链接；
- 不把评级当作事实；
- 失败不崩溃；
- 不接 Evidence Pack。

---

## MVP0-006：行情快照最小探针

任务编号：MVP0-006

任务名称：实现行情快照最小 probe

目标：
实现少量股票行情快照，为新闻 / 公告 / 研报关联后的报告提供市场反应。

允许新增 / 修改：

- 新增 `scripts/providers/quote_provider.py`
- 新增 `scripts/probes/test_quote_probe.py`
- 新增 `docs/probe_quote.md`
- 修改 `docs/current_progress.md`

输出文件：

- `data/raw/quote_probe_YYYYMMDD.json`
- `data/cache/quote_latest.json`

测试股票：

- `000001`
- `600000`
- `300750`
- `688981`

要求：

- 可参考 a-stock-data 的腾讯或 mootdx 行情思路；
- 只做小样本；
- 返回价格、涨跌幅、成交额、时间等字段。

运行方式：

```bash
python scripts/probes/test_quote_probe.py
```

---

## MVP0-007：股票 / 主题关联规则

任务编号：MVP0-007

任务名称：实现简化股票与主题关联规则

目标：
把新闻、公告、研报与股票代码 / 公司名 / 关键词做最小关联。

允许新增 / 修改：

- 新增 `scripts/utils/linking_utils.py`
- 新增 `scripts/probes/test_linking_rules.py`
- 修改 `data/manual/watchlist_symbols.txt`
- 修改 `data/manual/keyword_topics.json`
- 新增 `docs/linking_rules_mvp0.md`
- 修改 `docs/current_progress.md`

要求：

- 支持从文本中匹配 6 位股票代码；
- 支持从 watchlist 映射公司名；
- 支持关键词到主题映射；
- 不使用复杂 NLP。

运行方式：

```bash
python scripts/probes/test_linking_rules.py
```

---

## MVP0-008：构建 Fast Evidence Pack

任务编号：MVP0-008

任务名称：构建 Fast Evidence Pack

目标：
读取新闻、公告、研报、行情 cache，生成统一证据包。

允许新增 / 修改：

- 新增 `scripts/packs/build_fast_evidence_pack.py`
- 新增 `docs/fast_evidence_pack_schema.md`
- 修改 `docs/current_progress.md`

输入文件：

- `data/cache/eastmoney_news_latest.json`
- `data/cache/cninfo_announcement_latest.json`
- `data/cache/eastmoney_report_latest.json`
- `data/cache/quote_latest.json`

输出文件：

- `data/evidence/fast_evidence_pack_YYYYMMDD.json`
- `data/evidence/fast_evidence_pack_latest.json`

运行方式：

```bash
python scripts/packs/build_fast_evidence_pack.py
```

要求：

- 不直接请求外网；
- 只读取 cache；
- 包含 data_quality；
- 包含 sources；
- 包含 linked_items；
- 保留未匹配项。

---

## MVP0-009：生成 Markdown 报告

任务编号：MVP0-009

任务名称：生成 Markdown 热点分析报告

目标：
读取 Fast Evidence Pack，生成 Markdown 报告。

允许新增 / 修改：

- 新增 `scripts/reports/generate_markdown_report.py`
- 新增 `docs/report_template_mvp0.md`
- 修改 `docs/current_progress.md`

输入文件：

- `data/evidence/fast_evidence_pack_latest.json`

输出文件：

- `reports/fastlane_report_YYYYMMDD.md`
- `reports/fastlane_report_latest.md`

运行方式：

```bash
python scripts/reports/generate_markdown_report.py
```

要求：

- 报告必须包含数据质量说明；
- 必须区分事实、推测、待验证问题；
- 不输出买入 / 卖出建议；
- 不接 LLM。

---

## MVP0-010：一键运行脚本

任务编号：MVP0-010

任务名称：实现一键运行 FastLane pipeline

目标：
把 MVP-0 的 probe / pack / report 串起来，形成一键运行入口。

允许新增 / 修改：

- 新增 `scripts/run_fastlane_pipeline.py`
- 新增 `docs/runbook_mvp0.md`
- 修改 `docs/current_progress.md`

运行方式：

```bash
python scripts/run_fastlane_pipeline.py
```

要求：

- 每一步失败要记录，但不要无脑中断全部流程；
- 输出运行摘要；
- 生成最终报告；
- 不接自动交易；
- 不接 LLM。
