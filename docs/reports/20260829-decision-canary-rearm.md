# Decision Canary Rearm

- Implementation CI run: `33246836970`, Test/Lint PASS.
- Main and operating at rearm: `86b9fc44006c45431ccc1822131df3b4a74eb1ca`.
- Continuity entries: `4`, each with one BUY and one SELL directional claim.
- KR subjects: `003690`, `000660`.
- US subjects: `GOOGL`, `RXRX`.
- `DECISION_ENGINE_STATE = CANARY`.
- `PRODUCTION_CANARY_ENABLED = true`.
- Global decision block / non-canary visibility: `0 / 0`.
- KR / US natural canary cycles: `0/2 / 0/2`.

No scheduler, production recipient, task timing, assessment, DB, Pilot, Price Structure, valuation,
or market-message setting changed. Normal natural monitoring remains the only proof path.
