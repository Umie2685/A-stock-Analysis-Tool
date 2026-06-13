# 00_START_HERE：新项目启动入口

## 项目名称

建议名称：`AStockFastLane`

## 一句话目标

基于 `a-stock-data` 的数据源思路，快速开发一个 A 股热点分析工作流：自动抓取新闻、公告、研报、行情和主题信息，形成结构化证据包，并生成可读的热点分析报告。

## 为什么新开项目

旧项目已经形成了稳线：

```text
Tencent quote → CSV → Evidence Pack → Markdown 报告
mootdx → 候选行情增强 provider
```

现在新开项目的原因是：

```text
a-stock-data 覆盖面更广，适合快速逼近原始工具目标；
但它的数据源和端点很多，直接塞进旧项目会污染主线；
因此新项目独立开发，允许更快试错。
```

## 新项目定位

这是一个“快线项目”，目标是快速做出可运行工具，而不是一开始就追求完美架构。

但快线也必须有边界：

- 不做自动交易。
- 不做荐股结论。
- 不引导用户买卖。
- 不高频刷接口。
- 不整包复制第三方代码。
- 不绕过鉴权或风控。
- 不依赖单一数据源作结论。

## 第一阶段目标

MVP-0 目标：

```text
东财新闻 probe
+ 巨潮公告 probe
+ 东财研报 probe
+ 行情快照 probe
+ 结构化 Fast Evidence Pack
+ Markdown 报告
```

## 推荐执行顺序

```text
MVP0-001：项目骨架初始化
MVP0-002：接入 a-stock-data Skill 参考材料，只做本地文档，不复制整包
MVP0-003：东财新闻最小探针
MVP0-004：巨潮公告最小探针
MVP0-005：东财研报最小探针
MVP0-006：行情快照最小探针
MVP0-007：股票 / 主题关联规则
MVP0-008：Fast Evidence Pack
MVP0-009：Markdown 报告生成
MVP0-010：一键运行脚本
```

## ChatGPT 与 Codex 工作方式

你把 `09_CODEX_TASKS_MVP0.md` 中的任务逐条发给 Codex。每完成一条，把结果贴给 ChatGPT。ChatGPT 负责判断：

- 是否通过；
- 是否越界；
- 是否需要返工；
- 下一条任务是什么。
