# MVP3 Hot Events Quality Notes

Status: MVP3-005G completed

## Purpose

This note documents the quality upgrade for the offline hot-event analyzer. The goal is to make the output closer to a research-assistance report while staying strictly rule-based and local.

## Scope

Changed files:

- `config/concept_map.json`
- `scripts/analysis/analyze_hot_events.py`
- `scripts/run_web_dashboard.py`
- `README.md`
- `docs/current_progress.md`

Generated outputs:

- `data/analysis/hot_events_latest.json`
- `data/analysis/hot_events_YYYYMMDD.json`
- `reports/hot_events_latest.md`
- `reports/hot_events_YYYYMMDD.md`

## Concept Map Schema

Each concept now includes:

- `impact_logic`
- `typical_positive_triggers`
- `typical_negative_triggers`
- `risk_notes`

Each related stock now includes:

- `role`
- `relevance_score`
- `risk_note`

`relevance_score` is a 1-5 concept relevance score. It is not an investment value score.

## Analyzer Rules

The analyzer:

- Reads `data/evidence/fast_evidence_pack_latest.json`.
- Analyzes `news` evidence only.
- Reads concept definitions from `config/concept_map.json`.
- Keeps every news event, including events with no concept hit.
- Matches concepts by keyword and candidate watchlist links.
- Computes `impact_strength` from matched concept count, matched keyword count, and strong title trigger words.
- Sorts `high` events first, then `medium`, then `low`.
- Adds a rule-based `reason` for every event.
- Writes `analysis_level: rule_based`.

## Dashboard Upgrade

The local dashboard homepage now includes hot-event cards with:

- Title
- Event type
- Impact direction
- Impact strength
- Related concepts
- Candidate watchlist stocks
- Transmission logic
- Risk notes
- Rule reason
- `rule_based` analysis level

## Boundaries

MVP3-005G does not:

- Access the network
- Run probes
- Run `run_mvp2_pipeline.py`
- Download or parse PDFs
- Call an LLM
- Add third-party dependencies
- Connect K-line, order-book, or realtime quote data
- Add automatic trading
- Generate investment advice

The outputs are only for public-information organization and research assistance.
