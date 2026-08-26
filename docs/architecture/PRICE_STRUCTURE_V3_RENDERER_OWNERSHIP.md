# Price Structure v3 Renderer Ownership

## Contract

`price-structure-v3-renderer-ownership-v1` is a pure message-composition contract. It consumes
registered v3 zones and existing stored monitoring rules. It does not calculate prices, change
eligibility, or mutate a monitoring record.

## Owners

Every rendered price item has one owner:

| Owner | Meaning | Allowed content |
| --- | --- | --- |
| `CURRENT_PRICE_STRUCTURE` | Current completed-session OHLCV structure | nearest/major SR and eligible Fib/SR confluence |
| `STORED_MONITORING_PRICE_RULE` | Existing holder or monitoring management reference | confirmation, warning, invalidation, registered support |
| `VALUATION` | Existing valuation contract | valuation facts only |
| `OTHER` | Non-price supporting content | no v3 or stored-rule relabeling |

The current structure renders under `📐 현재 가격 구조`. Stored rules render under
`🧭 기존 등록 가격 규칙` and remain bound to `chart:stored_price_rules`. Proximity or overlap
does not merge ownership.

## Isolation

The contract is exercised by archive-only replay and tests. Production packets, Telegram,
fallback, Public Action, schema 4, tasks, assessments, and stored rules remain unchanged until a
separate selective-enablement task.
