# MVP3-006G Dashboard Hot Events Notes

## Scope

MVP3-006G enhances the local standard-library Dashboard display for existing hot-event analysis results.

The Dashboard reads local files only:

```text
data/analysis/hot_events_latest.json
reports/hot_events_latest.md
data/evidence/fast_evidence_pack_latest.json
reports/fast_report_latest.md
config/watchlist.json
```

It does not refresh data, run probes, call an LLM, download or parse PDFs, connect market data, or generate trading output.

## Homepage Additions

The homepage now includes:

- Hot-event total count.
- `high` / `medium` / `low` / `unknown` impact-strength counts.
- Matched concept list.
- Candidate watchlist count.
- Link to `/hot-events-report`.
- Rule-based analysis explanation.
- Data-health warnings when required local files are missing or unreadable.

## Hot Event Cards

Events are grouped by impact strength in this order:

```text
high
medium
low
unknown
```

Each card shows:

- Title.
- Event type.
- Impact direction.
- Impact strength.
- Related concepts.
- Candidate observation stocks.
- `relevance_score`.
- `matched_keywords`.
- `impact_logic`.
- `risk_notes`.
- `analysis_level`.
- URL.

Candidate observation stock rows show:

```text
code / name / role / relevance_score / reason / risk_note
```

These rows are research context only and are not buy, sell, or holding guidance.

## Report Preview

The `/hot-events-report` route previews:

```text
reports/hot_events_latest.md
```

The route renders Markdown source inside a `<pre>` block. It does not regenerate the report.

## Boundary

Allowed wording:

```text
candidate observation stocks
research assistance
risk notes
not investment advice
```

Forbidden wording remains excluded from Dashboard-authored page text:

```text
推荐买入
建议关注
投资机会
建议买入
建议增持
强烈推荐
收益承诺
稳赚
```
