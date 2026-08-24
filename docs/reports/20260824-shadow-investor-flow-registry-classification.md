# Shadow Investor-Flow Registry Classification

## Before And After

| Measure | Before | After |
|---|---:|---:|
| Registry entries | 1,440 | 1,425 |
| Registered | 1,230 | 1,425 |
| Unsupported | 210 | 0 |
| Prose eligible | 1,142 | 1,127 |
| Prose denied | 298 | 298 |

The post-repair packet contains 15 fewer entries because unsafe current macro-transmission numerics
are no longer emitted after temporal rehydration. Its classes are:

- `REGISTERED_PROSE_ELIGIBLE`: 1,127
- `REGISTERED_AUDIT_ONLY`: 88
- `REGISTERED_INTERNAL_DERIVED`: 210

Every reconciliation field has an exact actor/window semantic and `prose_allowed=false`. There are
no wildcard entries and no residual-derived participant prose claims.
