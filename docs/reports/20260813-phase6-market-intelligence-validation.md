# Phase 6 Market Intelligence Validation

Date: 2026-08-13 KST
Base: `a11049494c67415472c5067b3566edf66114f091`
AI policy: `daily-review-v3.6`
Output schema: `4`
Structure algorithm: `ohlcv-structure-v2`

## Scope and invariants

Phase 6 replaces method-heavy market prose with a deterministic market-fact and
portfolio-transmission contract. It does not change official assessments, the two
Knowledge bodies, the public Action schema, the chart engine, or the single-delivery
fallback policy.

- AI reads only backend packet facts and performs no web or provider collection.
- Market context can be a tailwind or headwind, but never changes a company thesis.
- Every market prose number uses the same exact-location numeric provenance as stock prose.
- Stale observations are excluded from the fact catalog and selected changes.
- Production Assist remains disabled.

## Market packet inventory

The immutable 2026-08-13 KR session was rebuilt from its original morning briefing and
assessment facts. US index and sector proxies are overnight context for KR, not Korean
local-market facts.

| Area | Status | Verified inputs or limitation |
|---|---|---|
| Indices | Available | SPY, QQQ, IWM; KR role is overnight cross-asset context |
| KR local indices | Unavailable | No KOSPI/KOSDAQ fact in the backend packet |
| Breadth | Unavailable | No advance/decline contract in the backend packet |
| Sector | Partial | SOXX only; KR role is overnight cross-asset context |
| Market flows | Unavailable | No market-wide foreign/institution/retail contract |
| Rates | Available | DGS10, DFII10, T10YIE |
| Credit | Available | BAMLH0A0HYM2 |
| FX | Available | USDKRW |
| Commodities | Available | WTI |
| Risk signal | Available | VIX |
| Broad dollar liquidity | Unavailable | DTWEXBGS was stale and excluded |
| Night futures | Available when supplied | Existing deterministic contract retained |

The same historical US packet classified SPY/QQQ/IWM as local market proxies, but breadth
and market-wide flows remained unavailable. Missing categories are explicit unknowns; the
service creates no placeholder numbers or inferred sector returns.

## Structured packet and selection

The packet now carries a session identity, coverage map, fact catalog, selected fact IDs,
verified portfolio exposure groups, allowed transmission candidates, and compact per-stock
market transmission. The 2026-08-13 KR session discovered seven session stocks and grouped
them from verified profiles:

| Group | Session tickers |
|---|---|
| Semiconductor | 000660 |
| Insurance/reinsurance | 003690 |
| Shipping/logistics | 086280 |
| Verified general/diversified | 005490, 005930, 010120, 012450 |

The selector chose two decisive verified changes:

1. SOXX relative to SPY: `+1.9228%p`
2. WTI return: `+3.4285%`

Twenty-nine prose-eligible market numeric anchors were available. The dry-run used nine
claims across the one-line judgment, key changes, market structure, and portfolio
transmission. Validation passed with no grounding flag.

## Numeric and transmission fencing

New explicit semantic contracts cover index and sector returns, relative performance,
nominal and real yields, breakeven inflation, credit spreads, FX, oil, VIX, and the broad
dollar index. Values remain fail closed: an index return cannot support a sector return,
a yield level cannot support a basis-point change, and a market flow cannot substitute for
a stock flow.

Every portfolio transmission must name an existing verified profile group and use a fact
explicitly allowed for that group. A transmission without a fact, with a foreign group, or
with an unrelated fact is rejected. Each accepted link records that it is market context,
not fundamental confirmation.

## Retrospective before and after

Before, the corrected v3.5 market message mainly said that only same-session facts were
used, price and business logic were separated, and later events were excluded. Those are
valid audit rules but do not explain the market.

After, the same immutable facts produce:

- two selected changes rather than a full metric dump;
- US cross-asset movement explicitly separated from unavailable KR breadth;
- semiconductor and shipping transmission with a fundamental-confirmation fence;
- conditional next checks;
- natural-language data limits without raw `quality=partial` or `stale` metadata.

The exact final text is stored in
`docs/reports/20260813-phase6-kr-market-intelligence-dry-run.md`. This retrospective was
archive-only: no Telegram message was sent, no assessment was changed, and no Pilot day
was counted.

## Renderer and quality gates

`ai-assisted-pilot-renderer-v3` renders one integrated market message with:

1. one-line judgment;
2. two to four important verified changes;
3. market structure;
4. portfolio transmission;
5. next confirmation;
6. material data limits.

It does not render `market_assumptions`, method narration, internal routing metadata, or a
second copy of the deterministic market report. Deterministic cautions remain archived; if
the AI already explains material unknowns, raw deterministic provider wording is not added
to Telegram.

Quality telemetry now includes:

- `insufficient_market_quantitative_grounding`
- `market_fact_without_transmission`
- `portfolio_transmission_without_fact`
- `generic_market_summary`

## Deployment gate

The four existing Scheduled Tasks keep their times and claim/fencing behavior. Activation
requires the exact pushed commit in the operating checkout and all four prompts updated to
`daily-review-v3.6`, output schema `4`, and renderer v3. Old v3.5/schema-3 outputs remain
history and cannot be delivered under the new policy.

Single delivery remains unchanged:

- validated AI result: AI-assisted set only;
- no valid result by deadline: deterministic fallback set only;
- late AI after fallback: archive only.

## Local validation

- Full pytest: 581 passed, 1 external Starlette deprecation warning
- Ruff: passed
- `git diff --check`: passed
- Output schema JSON: v4 / `daily-review-v3.6`
- Investment Knowledge v3 source/runtime checksum: unchanged and equal
- Chart Knowledge v1 source/runtime checksum: unchanged and equal
- Public Action: version 0.4.5, 20/20 unique operationIds
- DB migration: none
- Official assessment, NotificationDelivery, and Telegram: no retrospective mutation

## Remaining data gaps

The backend still has no KR local index, market breadth, or market-wide investor-flow facts
in the AI packet. Sector coverage is currently SOXX-only. These are explicit packet gaps,
not AI-reasoning gaps, and must be added as deterministic backend facts before the AI can
use them. Several verified diversified profiles remain in the general group, so their
transmission stays company-evidence-driven rather than being forced into a specialist group.
