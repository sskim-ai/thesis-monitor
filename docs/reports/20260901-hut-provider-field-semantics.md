# HUT Provider Field Semantics

| Normalized | Kiwoom field | Owner |
| --- | --- | --- |
| open | open_pric | COMPLETED_BAR |
| high | high_pric | COMPLETED_BAR |
| low | low_pric | COMPLETED_BAR |
| close | cur_prc | CURRENT_QUOTE for newest row |
| settled regular close | not exposed | UNAVAILABLE |
| finality | not exposed | UNCONFIRMED for newest row |

The official Kiwoom schema labels `cur_prc` as current price. The repository adapter previously mapped it to normalized close. Bounded observations changed from `81.9400` to the current replay specimen while O/H/L remained frozen, so mutable-quote ownership is evidenced rather than assumed. `HUT_PROVIDER_FIELD_SEMANTICS_MAPPED = PASS`.
