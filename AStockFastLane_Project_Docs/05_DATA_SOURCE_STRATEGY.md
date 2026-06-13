# 05_DATA_SOURCE_STRATEGY：数据源策略

## 总原则

本项目以 `a-stock-data` 作为数据源地图和接口参考，但每个接口都必须先在本项目中独立 probe。

## 数据源优先级

| 数据类型 | 首选方向 | 备选方向 | MVP-0 策略 |
|---|---|---|---|
| 新闻 | 东财新闻 / 全球资讯 | 财联社等 | 先做东财新闻 probe |
| 公告 | 巨潮资讯 | 交易所公告 | 先做公告列表，不下载全文 |
| 研报 | 东财研报 | 同花顺研报 | 先做列表 / 摘要 |
| 行情快照 | 腾讯 / mootdx | 其他 HTTP 源 | 先小样本 |
| K 线 | mootdx / 腾讯 / 百度 | 其他源 | 可选增强 |
| 盘口 | mootdx | 其他源 | 可选增强 |
| 题材热点 | 同花顺热点 | 东财概念 | MVP-1 |
| i问财 | 暂缓 | 无 | 不进 MVP-0 |

## 数据源接入流程

```text
1. 查阅 a-stock-data 的对应端点说明
2. 新建 probe 脚本
3. 限量请求 5～20 条
4. 保存 raw / cache JSON
5. 写 probe 文档
6. 验收通过后封装 provider
7. provider 通过后进入 Evidence Pack
```

## 字段标准化建议

### 新闻 item

```json
{
  "item_type": "news",
  "title": "",
  "publish_time": "",
  "source": "",
  "url": "",
  "summary": "",
  "related_symbols": [],
  "related_topics": [],
  "raw": {}
}
```

### 公告 item

```json
{
  "item_type": "announcement",
  "title": "",
  "publish_time": "",
  "company": "",
  "symbol": "",
  "url": "",
  "announcement_type": "",
  "raw": {}
}
```

### 研报 item

```json
{
  "item_type": "research_report",
  "title": "",
  "publish_time": "",
  "institution": "",
  "analyst": "",
  "symbol": "",
  "company": "",
  "rating": "",
  "url": "",
  "raw": {}
}
```

### 行情 item

```json
{
  "item_type": "quote",
  "symbol": "",
  "name": "",
  "price": null,
  "pct_change": null,
  "turnover": null,
  "source": "",
  "quote_time": "",
  "raw": {}
}
```

## 限流和安全策略

- 所有请求设置 timeout。
- 单次请求数量小于 20。
- 不做 while True 循环。
- 不做并发。
- 失败后记录错误，不无限重试。
- 文档记录来源和风险。
