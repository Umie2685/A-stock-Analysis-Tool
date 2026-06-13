# Current Progress

## MVP0-001

Status: Created project skeleton.

## Done

- Created base directories.
- Created placeholder configs.
- Created minimal IO utilities.
- Created project check script.

## Not Started

- Eastmoney news probe.
- CNInfo announcement probe.
- Eastmoney report probe.
- Fast Evidence Pack.
- Markdown report generation.

## MVP0-002

Status: Completed

Summary:

- Reviewed a-stock-data README.md / SKILL.md.
- Created docs/a_stock_data_reference.md.
- Identified MVP-0 candidate endpoints.
- Confirmed no third-party code was copied.

Next:

- MVP0-003: Eastmoney news minimal probe.

## MVP0-003

Status: Completed

Summary:

- Implemented Eastmoney news minimal probe.
- Generated raw/cache JSON.
- Updated endpoint probe results.

Next:

- MVP0-004: Fast Evidence Pack minimal generation.

## MVP0-003S

Status: Partially Completed

Summary:

- Attempted to install and verify a-stock-data Skill.
- Created installation notes.
- Created usage plan.
- Updated project direction to Skill-centric development.

Next:

- MVP0-004S: Use Skill to identify Eastmoney news endpoint.

## Eastmoney News Minimal Source Loop

Status: Completed

Summary:

- Confirmed Eastmoney global news endpoint from local installed a-stock-data SKILL.md.
- Implemented / aligned the minimal Eastmoney news probe with the Skill-documented endpoint shape.
- Generated raw/cache JSON for the news probe.
- Added docs/eastmoney_news_endpoint_notes.md.
- Updated endpoint probe results.

Next:

- MVP0-005G: Fast Evidence Pack minimal generation.

## MVP0-005G

Status: Completed

Summary:

- Built minimal Fast Evidence Pack from Eastmoney news probe.
- Generated latest and dated evidence JSON.
- No network request was made.

Next:

- MVP0-006G: Generate Markdown hotspot report.

## MVP0-006G

Status: Completed

Summary:

- Generated Markdown fast report from Fast Evidence Pack.
- Created latest and dated report files.
- No network request or LLM call was made.

Next:

- MVP0-007G: Add CNInfo announcement source.

## MVP0-007G

Status: Completed

Summary:

- Confirmed one CNInfo announcement endpoint from local a-stock-data SKILL.md.
- Implemented CNInfo announcement minimal probe.
- Generated raw/cache announcement JSON.
- No PDF download, Evidence Pack generation, report generation, or investment advice was produced.

Next:

- MVP0-008G: Merge CNInfo announcements into Fast Evidence Pack.

## MVP0-008G

Status: Completed

Summary:

- Merged Eastmoney news and CNInfo announcements into Fast Evidence Pack.
- Generated latest and dated evidence JSON.
- No network request was made.

Next:

- MVP0-009G: Upgrade Markdown report to support news + announcements.

## MVP0-009G+010G

Status: Completed

Summary:

- Upgraded Markdown report for news + announcements.
- Added one-click MVP0 pipeline runner.

Next:

- MVP0-011G: Prepare MVP0 release notes and README update.

## MVP0-011G

Status: Completed

Summary:

- Updated README for the completed MVP0 data chain.
- Created docs/mvp0_release_notes.md.
- Created docs/context_summary.md.
- Updated endpoint probe results with the MVP0 release documentation record.
- Extended project check coverage for the one-click pipeline and key report artifacts.

Next:

- MVP1-001G: 接入东财研报 probe
