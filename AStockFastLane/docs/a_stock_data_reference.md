# a-stock-data Reference Notes

## 1. Reference Source

- Repository: https://github.com/simonlin1212/a-stock-data
- README.md checked at: https://github.com/simonlin1212/a-stock-data/blob/main/README.md
- SKILL.md checked at: https://github.com/simonlin1212/a-stock-data/blob/main/SKILL.md
- Checked time: 2026-06-14 00:44:47 +08:00

## 2. Why We Reference It

AStockFastLane references a-stock-data because it provides a useful map of A-share data source layers, endpoint categories, and provider-style organization.

Useful ideas for this project:

- Data source layering across quotes, news, announcements, research reports, signals, capital flow, and fundamentals.
- Endpoint probe discipline before wrapping an interface as a provider.
- Provider output should be structured and report-friendly.
- Data source risk and throttling should be documented before use.

AStockFastLane does not copy a-stock-data as a whole package. This project will only use the repository as a reference for endpoint direction, parameter shape, field expectations, and risk notes. All MVP implementations must be written as small local probes first.

## 3. Data Layers Observed

The README / SKILL materials describe a broad A-share toolkit with these observed layers:

- Quotes / market data layer: mootdx, Tencent Finance, Baidu K-line, indexes, ETFs, quote snapshots, K-line, order book, valuation fields.
- News / information layer: Eastmoney individual stock news and Eastmoney global market news.
- Announcement layer: CNInfo announcements and related announcement retrieval.
- Research report layer: Eastmoney reportapi, report lists, report PDF direction, consensus expectation sources, iwencai search.
- Theme / hotspot / signal layer: Tonghuashun hotspots, reason tags, sector attribution, northbound flow, Eastmoney sector membership.
- Capital / chip layer: margin financing, block trades, shareholder count changes, dividends, capital flow.
- Fundamentals layer: quarterly snapshot fields, F10 company profile text, Eastmoney stock info, Sina financial statements.
- Other workflow layer: single-stock research, batch comparison, topic research, and multi-source research flows.

This section records observed layers only. No endpoint is implemented in MVP0-002.

## 4. MVP-0 Candidate Endpoints

数据源名称：Eastmoney news / global information

用途：Capture a small number of market news items for hotspot evidence.

可能字段：title, publish_time, source, url, summary, raw.

是否适合 MVP-0：Yes. It is a direct fit for the news probe and report evidence flow.

风险 / 注意事项：Eastmoney has rate-limit and intermittent risk notes. MVP-0 must use small request limits, timeout, no concurrency, and explicit error capture.

数据源名称：CNInfo announcements

用途：Capture announcement lists for company disclosure evidence.

可能字段：title, publish_time, company, symbol, announcement_type, url, raw.

是否适合 MVP-0：Yes. It is a core public disclosure source.

风险 / 注意事项：MVP-0 should only fetch announcement lists and links. Do not bulk-download PDFs or build a full announcement archive.

数据源名称：Eastmoney research reports

用途：Capture limited research report list / summary metadata as institutional-view evidence.

可能字段：title, publish_time, institution, analyst, symbol, company, rating, url, raw.

是否适合 MVP-0：Yes, with caution.

风险 / 注意事项：Ratings and institution opinions are not facts. Reports must be labeled as source opinions and should not be converted into investment advice.

数据源名称：Small quote snapshot

用途：Attach basic market reaction fields to linked stocks.

可能字段：symbol, name, price, pct_change, turnover, quote_time, source, raw.

是否适合 MVP-0：Yes, for a small watchlist only.

风险 / 注意事项：Prefer low-risk sources for quote snapshots where possible. Do not run full-market polling or high-frequency refresh.

数据源名称：Simple theme / hotspot attribution

用途：Map keywords, company names, and symbols into rough topics for report grouping.

可能字段：symbol, company, keyword, topic, evidence_source, confidence_note.

是否适合 MVP-0：Partially. Use local manual mapping and simple rules first.

风险 / 注意事项：Avoid complex NLP and avoid guessing unsupported stock-topic relationships.

## 5. Deferred Endpoints

Deferred endpoint groups and capabilities:

- i问财 / iwencai: requires API Key for semantic search and adds authentication / compliance complexity.
- High-frequency full-market crawling: outside MVP-0 and conflicts with the small-probe strategy.
- Complex capital flow: useful later but too broad for the first evidence pack.
- Batch Dragon Tiger List / 龙虎榜: defer until quote, news, announcement, and report basics are stable.
- Full PDF download: especially research reports and announcements; MVP-0 should record links instead.
- Automatic trading-related capability: permanently excluded from AStockFastLane.
- Interfaces requiring complex authentication or bypassing risk controls: excluded unless officially allowed and documented.
- Large-scale third-party data archiving: outside MVP-0 and requires additional compliance review.

## 6. License / Attribution / Compliance Notes

1. The GitHub repository page shows an Apache-2.0 license.
2. Attribution should be retained in AStockFastLane documentation when using endpoint ideas or architecture references from a-stock-data.
3. AStockFastLane avoids copying third-party code by writing small independent probes and providers.
4. This project only references endpoint direction, parameter structure ideas, field expectations, and source risk notes.
5. Later implementation must rewrite minimal request functions locally, with timeouts, small limits, error handling, and source notes.

Even with an open-source license, copying large sections of SKILL.md or embedding the whole package is not part of this project strategy.

## 7. AStockFastLane Usage Policy

可以参考：

- 数据源分层；
- endpoint 名称；
- headers / params 思路；
- 返回字段设计；
- provider 封装方式。

不可以：

- 整包复制；
- 大段复制代码；
- 绕过接口风控；
- 高频抓取；
- 自动交易；
- 生成投资建议。

## 8. Recommended Next Step

MVP0-003S：安装并验证 a-stock-data Skill

## 9. MVP0-003S Direction Update

As of 2026-06-14 01:07:43 +08:00, AStockFastLane project direction changed from "reference-only" to "Skill-centric development accelerator".

Updated principle:

- Use the installed a-stock-data Skill to accelerate endpoint discovery and adapter design.
- Keep AStockFastLane runtime code local, minimal, and auditable.
- Do not copy the whole Skill into `scripts/`.
- Do not blindly paste large third-party code blocks into this project.
- Prefer a hybrid route: Skill guides development; AStockFastLane owns local probes/adapters, raw/cache files, Evidence Pack, and reports.
