# 04_ARCHITECTURE：系统架构设计

## 总体架构

```text
公开数据源
  ├─ 东财新闻
  ├─ 巨潮公告
  ├─ 东财研报
  ├─ 腾讯 / mootdx 行情
  └─ 题材 / 行业 / 热点候选源
        ↓
probe scripts
        ↓
provider layer
        ↓
raw / cache files
        ↓
Fast Evidence Pack
        ↓
report generator
        ↓
Markdown 报告
```

## 分层说明

### 1. Probe 层

Probe 层只验证接口是否可用。

特点：

- 可以失败；
- 不影响主流程；
- 每次只抓少量样本；
- 输出 raw JSON 和 latest JSON；
- 记录字段、错误、空返回。

### 2. Provider 层

Provider 层把已经验证过的接口封装成稳定函数。

特点：

- 输入输出结构化；
- 有参数校验；
- 有 timeout；
- 有错误处理；
- 不返回裸 response；
- 不直接写报告。

### 3. Cache 层

Cache 层保存最新可用数据。

建议目录：

```text
data/raw/
data/cache/
data/evidence/
reports/
```

### 4. Evidence Pack 层

Evidence Pack 是所有数据进入报告前的统一结构。

它应该做到：

- 数据来源清楚；
- 字段含义清楚；
- 不塞入过大原始数据；
- 对报告友好；
- 包含 data_quality。

### 5. Report 层

报告层只读取 Evidence Pack，不直接访问外部数据源。

报告结构建议：

```text
1. 今日市场信息概览
2. 热点线索
3. 相关股票
4. 新闻证据
5. 公告证据
6. 研报证据
7. 行情反应
8. 风险与待验证问题
9. 数据质量说明
```

## 推荐项目目录

```text
AStockFastLane/
  README.md
  requirements.txt
  scripts/
    probes/
    providers/
    packs/
    reports/
    utils/
  data/
    raw/
    cache/
    evidence/
    manual/
  reports/
  docs/
  tests/
```

## 不建议的架构

不建议一开始就做：

- 数据库；
- Web UI；
- 多线程抓取；
- 定时任务；
- 大规模全市场抓取；
- 自动交易；
- 复杂插件体系。
