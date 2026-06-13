# a-stock-data Skill Usage Plan for AStockFastLane

## 1. New Project Direction

AStockFastLane will use a-stock-data Skill as the core development accelerator.

The Skill should guide endpoint discovery, request shape design, source risk notes, and normalized output planning. AStockFastLane should still keep its own local project code small, auditable, and scoped to the MVP workflow.

## 2. What We Will Use the Skill For

- Discover available A-share data source endpoints.
- Speed up endpoint probe design.
- Understand required params / headers.
- Compare Eastmoney / CNInfo / report source coverage.
- Accelerate provider implementation.
- Help define normalized fields for Evidence Pack.

## 3. What We Will Not Use It For

- No automatic trading.
- No investment advice.
- No high-frequency full-market crawling.
- No bypassing access control.
- No blind copying of third-party source code.
- No bulk PDF downloading in MVP-0.
- No direct report conclusions that are unsupported by local raw/cache evidence.

## 4. Runtime Dependency Decision

Recommended option:

```text
Option C: Hybrid: Skill guides development, AStockFastLane keeps local adapters.
```

Reason:

- The Skill is valuable as a development accelerator and endpoint map.
- AStockFastLane should avoid making a large external Skill file its direct runtime surface.
- Local adapters can keep timeout, request limits, output schema, data quality notes, and compliance boundaries explicit.
- Runtime dependencies can be added gradually only when a local adapter truly needs them.

## 5. Revised MVP Route

```text
MVP0-003S: Install and verify a-stock-data Skill
MVP0-004S: Use Skill to identify Eastmoney news endpoint
MVP0-005S: Implement Eastmoney news probe or adapter
MVP0-006S: Generate Fast Evidence Pack
MVP0-007S: Generate Markdown hotspot report
MVP0-008S: Add CNInfo announcement source
MVP0-009S: Add Eastmoney research report source
```

## 6. Risk Controls

- Use small request limits.
- Set explicit timeout for every request.
- Save raw/cache data for reproducibility.
- Do not run loop refresh jobs.
- Do not run high-frequency or full-market crawling.
- Do not generate stock recommendations.
- Do not generate automatic trading instructions.
- Do not bypass authentication, captcha, or platform risk controls.
- Reports must include: `本项目仅用于数据整理和研究辅助，不构成投资建议。`

