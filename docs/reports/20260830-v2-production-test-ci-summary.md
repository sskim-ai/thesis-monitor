# V2 Production Test and CI Summary

| Check | Result |
|---|---|
| Focused production/runtime suite | `76 passed` |
| Full pytest | `1955 passed, 1 deprecation warning` |
| Ruff | `PASS` |
| git diff --check | `PASS` |
| Investment Knowledge canonical/runtime | `dc747fff...c312 / identical` |
| Chart Knowledge canonical/runtime | `beee6455...e19b / identical` |
| Public Action | `0.4.5 unchanged` |
| operationId | `20/20 unique` |
| Implementation Actions | run `33299339989`, Test/Lint `PASS` |
| Premerge report Actions | run `33300809775`, Test/Lint `PASS` |
| Exact provenance Actions | run `33301030455`, Test/Lint `PASS` |
| Main exact-SHA Actions | run `33301218328`, Test/Lint `PASS` |

Main and operating are at the same promoted SHA. The final documentation closure receives a
separate exact-SHA run before final completion.
