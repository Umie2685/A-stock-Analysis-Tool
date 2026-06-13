# AStockFastLane

AStockFastLane 是一个 A 股热点数据整理与研究辅助工具。

本项目当前处于 MVP0 阶段，重点是打通一条小请求量、可复跑、可审计的数据整理链路：

```text
东财新闻 + 巨潮公告 -> Fast Evidence Pack -> Markdown 报告
```

本项目仅用于数据整理和研究辅助，不构成投资建议。

## MVP0 当前支持

- 东财全球资讯最小探针：抓取少量新闻数据并保存 raw/cache JSON。
- 巨潮公告最小探针：抓取单只示例股票的公告元数据，不下载 PDF。
- 多源 Fast Evidence Pack：合并新闻和公告缓存，生成统一证据 JSON。
- Markdown 报告：从 Evidence Pack 生成 news + announcement 两类内容的研究辅助报告。
- 一键运行脚本：按顺序执行新闻探针、公告探针、Evidence Pack、Markdown 报告。

## 当前不支持

- 不提供投资建议。
- 不做自动交易。
- 不下载公告 PDF。
- 不接入 LLM。
- 不提供 Streamlit / Web 页面。
- 不创建数据库。
- 不做高频抓取或循环刷新。
- 不做全市场批量遍历。

## 一键运行

从项目根目录运行：

```bash
python scripts/run_mvp0_pipeline.py
```

一键脚本会依次执行：

```text
scripts/probes/test_eastmoney_news_probe.py
scripts/probes/test_cninfo_announcement_probe.py
scripts/pipeline/build_fast_evidence_pack.py
scripts/pipeline/generate_fast_report.py
```

## 单独运行各步骤

```bash
python scripts/probes/test_eastmoney_news_probe.py
python scripts/probes/test_cninfo_announcement_probe.py
python scripts/pipeline/build_fast_evidence_pack.py
python scripts/pipeline/generate_fast_report.py
```

项目骨架检查：

```bash
python scripts/check_project.py
```

## 输出文件

新闻探针：

- `data/raw/eastmoney_news_probe_YYYYMMDD.json`
- `data/cache/eastmoney_news_probe_latest.json`

公告探针：

- `data/raw/cninfo_announcement_probe_YYYYMMDD.json`
- `data/cache/cninfo_announcement_probe_latest.json`

Evidence Pack：

- `data/evidence/fast_evidence_pack_YYYYMMDD.json`
- `data/evidence/fast_evidence_pack_latest.json`

Markdown 报告：

- `reports/fast_report_YYYYMMDD.md`
- `reports/fast_report_latest.md`

## 核心文档

- `docs/current_progress.md`：当前任务进度。
- `docs/endpoint_probe_results.md`：探针与流水线结果记录。
- `docs/mvp0_release_notes.md`：MVP0 发布说明。
- `docs/context_summary.md`：供后续开发或 `/compact` 使用的上下文摘要。
