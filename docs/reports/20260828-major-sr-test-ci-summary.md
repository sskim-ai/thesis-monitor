# Major S/R Test and CI Summary

| Validation | Result |
|---|---|
| Focused price-structure suite | `75 passed` |
| Full pytest | `1849 passed`, one upstream warning |
| Ruff | `PASS` |
| git diff --check | `PASS` |
| Knowledge parity | `PASS` |
| Public Action / schema | `0.4.5 / 4`, unchanged |
| operationId | `20/20`, unique |
| Implementation CI | run `33145205245`, Test/Lint PASS |
| Fixed-raw US/KR replay | `13/13 + 7/7 PASS` |
| Dedicated test delivery | `20/20 exact PASS` |
| Post-deploy replay | `20/20 PASS` |
