# KR Sector Breadth Numeric Semantics

The source fact type is `market_cross_section_sector`. Sector-index return and component counts are
independent semantic families.

| Exact path | Semantic | Registry class | Prose |
|---|---|---|---|
| `fields.listed_count` | `sector_listed_issue_count` | supported canonical | yes |
| `fields.advance_count` | `sector_advance_count` | supported canonical | yes |
| `fields.decline_count` | `sector_decline_count` | supported canonical | yes |
| `fields.unchanged_count` | `sector_unchanged_count` | supported canonical | yes |
| `fields.limit_up_count` | `sector_limit_up_count_audit` | audit only | no |
| `fields.limit_down_count` | `sector_limit_down_count_audit` | audit only | no |

Every row preserves owner `market_context`, `market_scope`, `sector_scope`, same-session basis,
source owner, unit `count`, and comparison eligibility. No `sector.*`, `breadth.*`, or `*.count`
wildcard exists.

Legacy sector fact IDs omitted market scope. Twenty same-name KOSPI/KOSDAQ pairs therefore collided.
Canonical identity now includes taxonomy, market scope, and sector code:

```text
market:cross-section:sector:{taxonomy}:{market_scope}:{sector_code}
```

Unknown future sector numeric paths remain `UNSUPPORTED_BLOCKING` and cannot enter prose.

