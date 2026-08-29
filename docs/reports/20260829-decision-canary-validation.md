# Decision Canary Validation

- Focused canary/config tests: `24 passed`
- Delivery/adaptive regression: `47 passed`
- Combined canary/delivery regression after continuity repair: `71 passed`
- Final focused suite including persistent documentation: `82 passed`
- Full pytest: `1901 passed, 1 warning`
- Ruff: `PASS`
- `git diff --check`: `PASS`
- Investment Knowledge SHA-256: `dc747fff856530e82477851cbd0bb16c5876770de514a9c02cfd5a26ac91c312`
- Chart Knowledge SHA-256: `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`
- Public Action: `0.4.5 unchanged`
- Output schema: `4 unchanged`
- operation IDs: `20/20 unique`
- User-visible non-canary behavior: `0 change`
- Manual production Telegram/task, Pilot, DB mutation: `0/0/0/0`
- Production Assist: `OFF`

Exact-SHA GitHub Actions results are recorded after branch and main promotion. Natural proof is
intentionally pending and is not replaced by manual execution.
