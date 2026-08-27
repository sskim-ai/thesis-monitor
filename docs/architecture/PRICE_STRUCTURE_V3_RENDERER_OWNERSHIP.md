# Price Structure v3 Renderer Ownership

## Contract

`price-structure-v3-renderer-ownership-v1` is a pure message-composition contract. It consumes
registered v3 zones and existing stored monitoring rules. It does not calculate prices, change
eligibility, or mutate a monitoring record.

## Owners

Every rendered price item has one owner:

| Owner | Meaning | Allowed content |
| --- | --- | --- |
| `CURRENT_PRICE_STRUCTURE` | Current completed-session OHLCV structure | user-visible near/major/long-horizon SR and eligible Fib/SR confluence |
| `STORED_MONITORING_PRICE_RULE` | Existing holder or monitoring management reference | confirmation, warning, invalidation, registered support |
| `VALUATION` | Existing valuation contract | valuation facts only |
| `OTHER` | Non-price supporting content | no v3 or stored-rule relabeling |

The current structure renders under `📐 현재 가격 구조`. Stored rules render under
`🧭 기존 등록 가격 규칙` and remain bound to `chart:stored_price_rules`. Proximity or overlap
does not merge ownership.

Internal nearest ownership is not a display label. Only canonical `NEAR/ACTIVE_NEAR` zones render
as `가까운`; `RELEVANT` and `LONG_HORIZON` use structural labels. Each visible SR line carries its
zone ID, source refs, distance, proximity tier, and active relevance. The renderer-output validator
rejects a line whose label and provenance disagree.

This proximity-aware surface is an explicit KR rollout mode. The renderer's default contract stays
legacy-compatible for existing non-KR shadow callers, so the bounded KR repair does not alter US
Price Structure output or eligibility.

Legacy suppression also has typed ownership. Structural fields are protected; current v3 and
stored rules are retained by their owners; only explicitly eligible legacy-technical prose is
token-scanned. The detector cannot suppress a company header or section heading.

## Isolation

`kr-price-structure-selective-rollout-v1` may compose this contract for monitored numeric KR
tickers only. It renders proximity-eligible SR plus family-consensus-safe Fib for `ELIGIBLE`, SR without
a Fib placeholder for `ELIGIBLE_SR_ONLY`, and no section for `OMIT_PRICE_STRUCTURE` or `BLOCKED`.
Omission never invalidates the rest of the stock message.

The guarded runtime path keeps the same current section in deterministic fallback and AI/adaptive
candidate output. All rendered numbers carry backend numeric references. The renderer does not
invent a target, stop, confirmation, invalidation, or monitoring rule. US and unmonitored subjects
remain outside this route.

`KR_PRICE_STRUCTURE_V3_ENABLED` defaults OFF. Production packets, Telegram, Public Action, schema
4, tasks, assessments, and stored rules remain unchanged until the dedicated-test-sink gate passes
and a separate KR-only enablement action sets the guard.
