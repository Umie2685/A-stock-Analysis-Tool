# CNInfo Announcement Endpoint Notes

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

The local SKILL.md documents CNInfo announcements as:

```text
https://www.cninfo.com.cn/new/hisAnnouncement/query
```

The SKILL notes that CNInfo `orgId` should be resolved correctly. To keep MVP0-007G to one data endpoint, the probe uses the SKILL-documented sample stock `688017` and its known orgId `9900041602`, rather than making an additional orgId mapping request.

## 3. Final Selected Endpoint

Endpoint:

```text
https://www.cninfo.com.cn/new/hisAnnouncement/query
```

Method:

```text
POST
```

Reason:

- It is explicitly documented in the installed a-stock-data SKILL.md under CNInfo announcements.
- It returns announcement metadata without downloading PDF files.
- It can be probed with one request and a small `pageSize`.
- It does not require an API key.

## 4. Headers

Probe headers:

```text
User-Agent: browser-like UA string
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Accept: application/json,text/plain,*/*
Origin: https://www.cninfo.com.cn
Referer: https://www.cninfo.com.cn/new/disclosure
```

## 5. Params

Probe form params:

```text
stock=688017,9900041602
tabName=fulltext
pageSize=10
pageNum=1
column=sse
category=
plate=sh
seDate=
searchkey=
secid=
sortName=
sortType=
isHLtitle=true
```

Notes:

- `pageSize` is capped at 10 in the current probe.
- The probe does not download PDFs.
- The probe does not fetch a separate orgId mapping endpoint.

## 6. Returned Field Mapping

Observed / expected response path:

```text
announcements[]
```

Standardized item mapping:

```text
title             <- item.announcementTitle
publish_time      <- item.announcementTime, converted from Unix milliseconds to YYYY-MM-DD
company           <- item.secName
symbol            <- item.secCode
announcement_type <- item.announcementTypeName
url               <- generated CNInfo disclosure detail URL from announcementId
raw               <- full item object
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

- CNInfo endpoint parameters may change.
- `orgId` mapping is important for stock-specific announcement queries.
- Use small request limits.
- Set explicit timeout.
- Do not run concurrent requests.
- Do not loop refresh.
- Do not full-market crawl.
- Do not download announcement PDFs in MVP0-007G.
- Record errors in JSON rather than hiding failures.
- This source is only evidence input; it must not be turned into investment advice.

