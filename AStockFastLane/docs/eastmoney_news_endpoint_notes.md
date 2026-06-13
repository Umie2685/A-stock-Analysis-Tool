# Eastmoney News Endpoint Notes

## 1. Skill Recognition

Active skill list recognition: not confirmed in this running Codex session.

Reason:

- `a-stock-data` was installed after this thread had already started.
- The installed Skill directory exists, but the active skill list in this session did not refresh to include `a-stock-data`.

Fallback used:

- Read local installed Skill file directly:
  `C:\Users\Administrator\.codex\skills\a-stock-data\SKILL.md`
- Read local installed README directly:
  `C:\Users\Administrator\.codex\skills\a-stock-data\README.md`

## 2. Candidate Endpoint

The local SKILL.md documents Eastmoney global 7x24 news as:

```text
https://np-weblist.eastmoney.com/comm/web/getFastNewsList
```

The same section describes this source as Eastmoney global finance information / 7x24 rolling news and as the replacement direction for deprecated CLS flash news.

## 3. Final Selected Endpoint

Endpoint:

```text
https://np-weblist.eastmoney.com/comm/web/getFastNewsList
```

Method:

```text
GET
```

Reason:

- It is explicitly documented in the installed a-stock-data SKILL.md under Eastmoney global news.
- It returns small, list-shaped fast news items suitable for MVP raw/cache validation.
- It does not require an API key.
- It can be probed with one request and a small `pageSize`.

## 4. Headers

Probe headers:

```text
User-Agent: browser-like UA string
Referer: https://kuaixun.eastmoney.com/
Accept: application/json,text/plain,*/*
```

## 5. Params

Probe params:

```text
client=web
biz=web_724
fastColumn=102
sortEnd=
pageSize=10
req_trace=<generated uuid>
```

Notes:

- `req_trace` is required by the endpoint and is generated per run.
- `pageSize` is capped at 10 in the current probe.
- `sortEnd` is present but empty for the first page, matching the local SKILL.md example.

## 6. Returned Field Mapping

Observed / expected response path:

```text
data.fastNewsList[]
```

Standardized item mapping:

```text
title        <- item.title
publish_time <- item.showTime
source       <- item.source / item.mediaName / fallback "eastmoney"
url          <- item.url / item.arturl / item.link / generated from item.code
summary      <- item.summary
raw          <- full item object
```

Top-level probe output:

```text
source
probe_name
fetched_at
endpoint
success
item_count
items
errors
```

## 7. Risk and Rate Limit Notes

- Eastmoney endpoints may have rate-limit or intermittent network risk.
- Use small request limits.
- Set explicit timeout.
- Do not run concurrent requests.
- Do not loop refresh.
- Do not perform full-market crawling.
- Record errors in JSON rather than hiding failures.
- This source is only evidence input; it must not be turned into investment advice.

