# Eastmoney Report Endpoint Notes

## 1. Skill Usage

- Active skill recognized: yes, `a-stock-data` is available in the current Codex skill list.
- Local Skill file read: `C:\Users\Administrator\.codex\skills\a-stock-data\SKILL.md`.
- Local README read: `C:\Users\Administrator\.codex\skills\a-stock-data\README.md`.
- Reference section: Layer 2, Eastmoney reportapi.

## 2. Candidate Endpoint

- Eastmoney reportapi report list:
  - `https://reportapi.eastmoney.com/report/list`

The Skill also documents Eastmoney PDF URL construction, but MVP1-001G does not download PDFs.

## 3. Selected Endpoint

- Endpoint: `https://reportapi.eastmoney.com/report/list`
- Method: `GET`
- Reason:
  - It returns research-report list metadata.
  - It can be queried for a single stock.
  - It supports small `pageSize` limits.
  - It does not require PDF download for MVP1-001G.

## 4. Headers and Params

Headers:

- `User-Agent`: browser-like desktop User-Agent.
- `Referer`: `https://data.eastmoney.com/`.
- `Accept`: `application/json,text/plain,*/*`.

Params:

- `industryCode=*`
- `pageSize=10`
- `industry=*`
- `rating=*`
- `ratingChange=*`
- `beginTime=2000-01-01`
- `endTime=2030-01-01`
- `pageNo=1`
- `fields=`
- `qType=0`
- `orgCode=`
- `code=688017`
- `rcode=`
- `p=1`
- `pageNum=1`
- `pageNumber=1`

## 5. Field Mapping

- `title` <- `title` / `reportTitle`
- `publish_time` <- `publishDate` / `publishTime`
- `institution` <- `orgSName` / `orgName`
- `analyst` <- `researcher` / `author`
- `company` <- `stockName` / `securityName`
- `symbol` <- `stockCode` / `code`
- `rating` <- `emRatingName` / `ratingName`
- `url` <- `url` / `reportUrl` / `webUrl`, or constructed from `infoCode`
- `summary` <- `summary` / `abstract` / `digest`
- `raw` <- original record

## 6. Risk and Rate-limit Notes

- Eastmoney endpoints may have access-frequency controls.
- This probe uses one endpoint, one request, no concurrency, no loop, and `pageSize=10`.
- The probe sets an explicit timeout.
- If the endpoint changes structure, the probe records parsing errors in the `errors` field instead of crashing without output.

## 7. Compliance Notes

- Research reports are stored only as institution-view metadata.
- Ratings and report titles are not converted into investment advice.
- No PDF is downloaded.
- No report body is parsed.
- No provider, Evidence Pack, Markdown report, LLM call, or automatic trading code is added in MVP1-001G.
