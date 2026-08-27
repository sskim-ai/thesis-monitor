# KR Final Price Structure Enablement

`KR_PRICE_STRUCTURE_ENABLED = false`

The Price Structure stage did not start. KR and US runtime behavior remain unchanged.

| Gate | Result |
| --- | --- |
| KR flag write | `0` |
| `POST_KR_PRICE_STRUCTURE_ENABLE` | `NOT_RUN` |
| `US_PRICE_STRUCTURE_ENABLED` | `0` |
| `POST_ENABLE_US_PRICE_STRUCTURE_LEAK` | `0` |
| US market digest code diff | `0` |

Future rollback is independent: set `kr_price_structure_v3_enabled=false` through the approved
configuration procedure. No rollback command was executed here.
